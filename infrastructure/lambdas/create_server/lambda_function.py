# Provisions a new Minecraft server for the authenticated user
import json
import logging
import os
import uuid
from datetime import daytime, timezone
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

from squadhost_common.user_data import INSTANCE_TYPE_MAP, build_user_data

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
ec2_client = boto3.resource("ec2")

TABLE_NAME = os.environ["SERVERS_TABLE"]
S3_BUCKET = os.environ["S3_BACKUP_BUCKET"]
WORKER_AMI_ID = os.environ["WORKER_AMI_ID"]
SECURITY_GROUP_ID = os.environ["SECURITY_GROUP_ID"]
SUBNET_ID = os.environ["SUBNET_ID"]
INSTANCE_PROFILE = os.environ["INSTANCE_PROFILE"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]
AWS_DEPLOY_REGION = os.environ["AWS_DEPLOY_REGION"]
PLAYITGG_SECRET_NAME = os.environ["PLAYITGG_SECRET_NAME"]

table = dynamodb.Table(TABLE_NAME)

# Handles POST request for /servers, Will validate input, write to the DB, Create the EC2 with minecraft docker image
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:

    # Auth
    try:
        owner_id: str = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]

    except KeyError:
        logger.error(json.dumps({"event": "missing_jwt_claims"}))
        return _response(401, {"error": "Missing or invalid authentication"})

    # Input Parsing
    try:
        body: Dict[str, Any] = json.loads(event.get("body") or "{}")

    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON body"})

    server_name: str = body.get("server_name", "").strip()
    if not server_name:
        return _response(400, {"error": "server_name is required"})

    try:
        ram_tier = int(body.get("ram_tier", 4))

    except (TypeError, ValueError):
        return _response(400, {"error": "ram_tier must be a number"})

    if ram_tier not in INSTANCE_TYPE_MAP:
        return _response(400, {"error": f"ram_tier must be one of {list(INSTANCE_TYPE_MAP.keys()}"})

    mc_version: str = body.get("mc_version", "LATEST")
    difficulty: str = body.get("difficulty", "normal")
    max_players: int = int(body.get("max_players", 20))
    allow_tlauncher: bool = bool(body.get("allow_tlauncher", False))
    seed: str = body.get("seed", "")

    # server_name uniqueness per owner
    try:
        existing = table.query(
            KeyConditionExpression="owner_id = :oid",
            FilterExpression="server_name = :name",
            ExpressionAttributeValues={
                ":oid": owner_id,
                ":name": server_name,
            },
        )

    except ClientError as exc:
        logger.error(json.dumps({
            "event": "dynamodb_name_check_failed",
            "owner_id": owner_id,
            "error": str(exc),
        }))
        return _response(500, {"error": "Failed to validate server name"})

    if existing.get("Count", 0) > 0:
        return _response(409, {"error": "You already have a server with that name"})

    # Write the initial DynamoDB record, server_id will be used as the immutable UUID evrywhere
    server_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    try:
        table.put_item(Item={
            "owner_id": owner_id,
            "server_id": server_id,
            "server_name": server_name,
            "mc_version": mc_version,
            "difficulty": difficulty,
            "max_players": max_players,
            "allow_tlauncher": allow_tlauncher,
            "seed": seed,
            "ram_tier": ram_tier,
            "status": "PROVISIONING",
            "created_at": now,
            "updated_at": now,
        })

    except ClientError as exc:
        logger.error(json.dumps({
            "event": "dynamodb_put_failed",
            "owner_id": owner_id,
            "server_id": server_id,
            "error": str(exc),
        }))
        return _response(500, {"error": "Failed to create server record"})

    # EC2 with Minecraft Server Launch
    online_mode = "FALSE" if allow_tlauncher else "TRUE"
    s3_world_key = f"worlds/{owner_id}/{server_id}/world.zip"

    user_data = _build_user_data(
        owner_id=owner_id,
        server_id=server_id,
        mc_version=mc_version,
        difficulty=difficulty,
        max_players=max_players,
        online_mode=online_mode,
        seed=seed,
        ram_tier=ram_tier,
        s3_bucket=S3_BUCKET,
        s3_world_key=s3_world_key,
        webhook_url=WEBHOOK_URL,
        region=AWS_DEPLOY_REGION,
        playitgg_secret_name=PLAYITGG_SECRET_NAME,
    )

    try:
        ec2_resposne = ec2_client.run_instances(
            ImageId=WORKER_AMI_ID,
            InstanceType=INSTANCE_TYPE_MAP[ram_tier],
            MinCount=1,
            MaxCount=1,
            SecurityGroupIds=[SECURITY_GROUP_ID],
            SubnetId=SUBNET_ID,
            IamInstanceProfile={"Name": INSTANCE_PROFILE},
            UserData=user_data,
            TagSpecifications=[{
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Name", "Value": f"squadhost-worker-{server-id}"},
                    {"Key": "project", "Value": "squadhost"},
                    {"Key": "server_id", "Value": server_id},
                    {"Key": "owner_id", "Value": owner_id},
                ]
            }]
        )

    # Rollback DynamoDB record for a failed Minecraft launch
    except ClientError as exc:
        logger.error(json.dumps({
            "event": "ec2_launch_failed",
            "owner_id": owner_id,
            "server_id": server_id,
            "error": str(exc),
        }))
        _rollback_db_record(owner_id, server_id)
        return _response(500, {"error": "Failed to launch server instance"})

    instance_id: str = ec2_resposne["Instances"][0]["InstanceId"]

    # Write Instance_id into DynamoDB
    try:
        table.update_item(
            Key={"owner_id": owner_id, "server_id": server_id},
            UpdateExpression="SET instance_id = :iid, updated_at =:now",
            ExpressionAttributeValues={
                ":iid": instance_id,
                ":now": datetime.now(timezone.utc).isoformat(),
            },
        )

    except ClientError as exc:
        logger.info(json.dumps({
            "event": "create_server_success",
            "owner_id": owner_id,
            "server_id": server_id,
            "instance_id": instance_id,
            "error": str(exc),
        }))

    logger.info(json.dumps({
        "owner_id": owner_id,
        "event": "create_server_success",
        "server_id": server_id,
        "instance_id": instance_id,
        "instance_type": INSTANCE_TYPE_MAP[ram_tier],
    }))

    return _response(202, {
        "server_id": server_id,
        "status": "PROVISIONING",
        "message": "Server is being provisioned. Poll get_server for status updates"
    })

# Deletes the failed Minecraft launch records
def _rollback_db_record(owner_id: str, server_id: str) -> None:

    try:
        table.delete_item(Key={"owner_id": owner_id, "server_id": server_id})
        logger.info(json.dumps({
            "event": "rollback_success",
            "owner_id": owner_id,
            "server_id": server_id,
        }))

    except ClientError as exc:
        logger.error(json.dumps({
            "event": "rollback_failed",
            "owner_id": owner_id,
            "server_id": server_id,
            "error": str(exc),
        }))

def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
