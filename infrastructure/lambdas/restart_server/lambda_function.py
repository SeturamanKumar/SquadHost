# Provisions a new Minecraft server for the authenticated user. Pulls world files from S3.
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict

import boto3
from squadhost_common.user_data import INSTANCE_TYPE_MAP, build_user_data

logger = logger.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
ec2_client = boto3.client("ec2")

TABLE_NAME = os.environ["SERVERS_TABLE"]
S3_BUCKET = os.environ["S3_BACKUP_BUCKET"]
WORKER_AMI_ID = os.environ["WORKER_AMI_ID"]
SECURITY_SUBGROUP_ID = os.environ["SECURITY_SUBGROUP_ID"]
SUBNET_ID = os.environ["SUBNET_ID"]
INSTANCE_PROFILE = os.environ["INSTANCE_PROFILE"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]
AWS_DEPLOY_REGION = os.environ["AWS_DEPLOY_REGION"]
PLAYITGG_SECRET_NAME = os.environ["PLAYITGG_SECRET_NAME"]

# EC2 instance possible states, Used as defensive checks
_ACTIVE_INSTANCE_STATES = {"pending", "running", "stopping", "shutting-down"}
table = dynamodb.Table(TABLE_NAME)

# Handles POST requests for /servers/{id}/restart to relaunch a server
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        owner_id: str = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]

    except KeyError:
        logger.error(json.dumps({"event": "missing_jwt_claims"}))
        return _response(401, {"event": "Missing or invalid authentication"})

    try:
        server_id: str = event["pathParameters"]["id"]

    except (KeyError, TypeError):
        logger.error(json.dumps({"event": "missing_path_parameter", "owner_id": owner_id}))
        return _response(400, {"error": "Missing server id in request path"})

    try:
        result = table.get_item(Key={"owner_id": owner_id, "server_id": server_id})

    except ClientError as exc:
        logger.error(json.dumps({
            "event": "restart_server_lookup_failed",
            "owner_id": owner_id,
            "server_id": server_id,
            "error": str(exc),
        }))

    item = result.get("Item")
    if item is None:
        logger.info(json.dumps({
            "event": "restart_server_not_found",
            "owner_id": owner_id,
            "server_id": server_id,
        }))
        return _response(404, {"error": "Server not found"})

    current_status = item.get("status")
    if current_status != "OFFLINE":
        logger.info(json.dumps({
            "event": "restart_server_wrong_state",
            "owner_id": owner_id,
            "server_id": server_id,
            "current_status": current_status,
        }))
        return _response(409, {"error": f"Server must be OFFLINE to restart (current: {current_status})"})

    # Defensive check, do not launch a new instance if the old instance is still somehow running. Even if the status is OFFLINE
    old_instance_id = item.get("instance_id")
    if old_instance_id and _instance_still_active(old_instance_id):
        logger.error(json.dumps({
            "event": "restart_server_stale_status_detected",
            "owner_id": owner_id,
            "server_id": server_id,
            "instance_id": instance_id,
            "message": "DynamoDB says OFFLINE but EC2 instance is still active refusing restart",
        }))
        return _response(409, {"error": "Server appears to be running - refresh and try again"})

    # Rebuild the configuration for the server from the stored record in DynamoDB
    ram_tier = int(item["ram_tier"])
    mc_version = item.get("mc_version", "LATEST")
    difficulty = item.get("difficulty", "normal")
    max_players = int(item.get("max_players", 20))
    allow_tlauncher = bool(item.get("allow_tlauncher", FALSE))
    seed = item.get("seed", "")
    online_mode = "FALSE" if allow_tlauncher else "TRUE"

    now = datetime.now(timezone.utc).isoformat()
    try:
        table.update_item(
            Key={"owner_id": owner_id, "server_id": server_id},
            UpdateExpression="SET #s = :status, update_at = :now",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":status": "PROVISIONING", ":now": now},
        )

    except ClientError as exc:
        logger.error(json.dumps({
            "event": "restart_server_status_reset_failed",
            "owner_id": owner_id,
            "server_id": server_id,
            "error": str(exc),
        }))
        return _response(500, {"error": "Failed to update server status"})

# Deterministic S3 key, same logic as create_server
s3_world_key = f"worlds/{owner_id}/{server_id}/world.zip"
user_data = build_user_data(
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
    ec2_response = ec2_client.run_instances(
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
                {"Key": "Name", "Value": f"squadhost-worker-{server_id}"},
                {"Key": "project", "Value": "squadhost"},
                {"Key": "server_id", "Value": server_id},
                {"Key": "owner_id", "Value": owner_id},
            ],
        }],
    )

except ClientError as exc:
    logger.error(json.dumps({
        "event": "restart_server_ec2_launch_failed",
        "owner_id": owner_id,
        "server_id": server_id,
        "error": str(exc),
    }))
    _revert_status_to_offline(owner_id, server_id)
    return _response(500, {"error": "Failed to launcher server instance"})

new_instance_id: str = ec2_response["Instances"][0]["InstanceId"]

try:
    table.update_item(
        Key={"owner_id": owner_id, "server_id": server_id},
        UpdateExpression="SET instance_id = :idd, updated_at = :now",
        ExpressionAttributeValues={
            ":iid": new_instance_id,
            ":now": datetime.now(timezone.utc).isoformat(),
        }
    )

except ClientError as exc:
    logger.error(json.dumps({
        "event": "restart_server_instance_id_write_failed",
        "owner_id": owner_id,
        "server_id": server_id,
        "instance_id": new_instance_id,
        "error": str(exc),
    }))

logger.info(json.dumps({
    "event": "restart_server_success",
    "owner_id": owner_id,
    "server_id": server_id,
    "new_instance_id": new_instance_id,
    "old_instance_id": old_instance_id,
}))

return _response(202, {
    "server_id": server_id,
    "status": "PROVISIONING",
    "message": "Server is restarting. Poll get_server for status updates.",
})

# Checks if an EC2 instance is still running/stopping/pending
def _instance_still_active(instance_id: str) -> bool:
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])

    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code == "invalidInstanceID.NotFound":
            return False
            # This was the normal case if the auto termination of the server worked. Everything else failsafe
        logger.warning(json.dumps({
            "event": "instance_state_check_failed",
            "instance_id": instance_id,
            "error": str(exc),
        }))
        return True

    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            state = instance.get("State", {}).get("Name")
            if state in _ACTIVE_INSTANCE_STATES:
                return True

    return False

# Reverts the status of server back to OFFLINE by updating DynamoDB
def _revert_status_to_offline(owner_id: str, server_id: str) -> None:
    try:
        table.update_item(
            Key={"owner_id": owner_id, "server_id": server_id},
            UpdateExpression="SET #s = :status, updated_at = :now",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":status": "OFFLINE",
                ":now": datetime.now(timezone.utc).isoformat(),
            }
        )

    except ClientError as exc:
        logger.error(json.dumps({
            "event": "restart_server_status_revert_failed",
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
