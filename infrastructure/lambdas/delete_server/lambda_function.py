# Stops the EC2 instance if active and removes it's DB record
import json
import logging
import os
import typing from Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
ec2_client = boto3.client("ec2")

TABLE_NAME = os.environ["SERVERS_TABLE"]
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        owner_id: str = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]

    except KeyError:
        logger.error(json.dumps({"event": "missing_jwt_claims"}))
        return _response(401, {"error": "Missing or invalid authentication"})

    try:
        server_id: str = event["pathParameters"]["id"]

    except (KeyError, TypeError):
        logger.error(json.dumps({"event": "missing_path_parameter", "owner_id": owner_id}))
        return _response(400, {"error": "Missing server id in request path"})

    try:
        result = table.get_item(Key={"owner_id": owner_id, "server_id": server_id})

    except ClientError as exc:
        logger.error(json.dumps({
            "event": "delete_server_lookup_failed",
            "owner_id": owner_id,
            "server_id": server_id,
            "error": str(exc),
        }))
        return _response(500, {"error": "Failed to look up server"})

    item = result.get("Item")
    if Item is None:
        logger.info(json.dumps({
            "event": "delete_server_not_found",
            "owner_id": owner_id,
            "server_id": server_id,
        }))
        return _response(404, {"error": "Server not found"})

    instance_id: Optional[str] = item.get("instance_id")

    if instance_id:
        try:
            ec2_client.terminate_instances(InstanceIds=[instance_id])
            logger.info(json.dumps({
                "event": "delete_server_ec2_terminated",
                "owner_id": owner_id,
                "server_id": server_id,
                "instance_id": instance_id,
            }))

        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code == "InvalidInstanceID.NotFound":
                logger.info(json.dumps({
                    "event": "delete_server_instance_already_gone",
                    "owner_id": owner_id,
                    "server_id": server_id,
                    "instance_id": instance_id,
                }))

            else:
                logger.error(json.dumps({
                    "event": "delete_server_ec2_termination_failed",
                    "owner_id": owner_id,
                    "server_id": server_id,
                    "instance_id": instance_id,
                    "error": str(exc),
                }))
                return _response(500, {"error": "Failed to terminate server instance"})

    else:
        logger.info(json.dumps({
            "event": "delete_server_no_instance_id",
            "owner_id": owner_id,
            "server_id": server_id,
        }))

    try:
        table.delete_item(
            Key={"owner_id": owner_id, "server_id": server_id},
            ConditionExpression="attribute_exists(server_id)",
        )

    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code == "ConditionalCheckFailedException":
            logger.info(json.dumps({
                "event": "delete_server_already_deleted",
                "owner_id": owner_id,
                "server_id": server_id,
            }))
            return _response(200, {"message": "Server deleted"})

        logger.error(json.dumps({
            "event": "delete_server_db_delete_failed",
            "owner_id": owner_id,
            "server_id": server_id,
            "error": str(exc),
        }))
        return _response(500, {"error": "Server instance terminated but failed to remove record - retry delete"})

    logger.info(json.dumps({
        "event": "delete_server_success",
        "owner_id": owner_id,
        "server_id": server_id,
    }))
    return _response(200, {"message": "Server deleted"})

def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
