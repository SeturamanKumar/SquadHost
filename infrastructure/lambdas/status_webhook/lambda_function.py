# Used to pass along the status update triggered by the Minecraft server, and the status update trigger by world save in S3
import json
import logging
import os
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ["SERVERS_TABLE"]
GSI_NAME = os.environ("SERVER_ID_INDEX", "server_id-index")
table = dynamodb.Table(TABLE_NAME)

VALID_STATUSES = { "PROVISIONING", "INSTALLING", "STARTING", "BOOTING", "ONLINE", "STOPPING", "OFFLINE", }

# Route the event based on where the lambda was triggered from (Minecraft server or S3)
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    if "Records" in event and event["Records"]:
        return _handle_s3_event(event)

    if "requestContext" in event:
        return _handle_webhook_request(event)

    logger.error(json.dumps({"event": "unrecognized_event_shape"}))
    return {"statusCode": 400, "body": "Unrecognized event shape"}

# S3 world-save confirmation trigger
def _handler_s3_event(event: Dict[str, Any]) -> Dict[str, Any]:
    try:
        record = event["Records"][0]["s3"]
        object_key = urllib.parse.unquote_plus(record["object"]["key"])

    except (KeyError, IndexError):
        logger.error(json.dumps({"event": "s3_invalid_record_structure"}))
        return {"statusCode": 400, "body": "Invalid S3 event structure"}

    parts = object_key.split("/")
    if len(parts) != 4 or parts[0] != "worlds" or not object_key.endswith(".zip"):
        logger.warning(json.dumps({
            "event": "s3_unexpected_key_format",
            "object_key": object_key,
        }))
        return {"statusCode": 400, "body": "Unexpected object key format"}

    _, owner_id, server_id, _ = parts

    try:
        table.update_item(
            Key={"owner_id": owner_id, "server_id": server_id},
            UpdateExpressions="SET world_saved_at = :ts, updated_at = :ts",
            ExpressionAttributeValues={":ts": datetime.now(timezone.utc).isoformat()},
            ConditionExpression="attribute_exists(server_id)",
        )

    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code == "ConditionalCheckFailedException":
            logger.warning(json.dumps({
                "event": "s3_world_save_unknown_server",
                "owner_id": owner_id,
                "server_id": server_id,
                "object_ket": object_key,
            }))
            return {"statusCode": 404, "body": "Server Not Found"}

        logger.error(json.dumps({
            "event": "s3_world_save_update_failed",
            "owner_id": owner_id,
            "server_id": server_id,
            "error": str(exc),
        }))
        return {"statusCode": 500, "body": "Failed to record world save"}

    logger.info(json.dumps({
        "event": "world_save_confirmed",
        "owner_id": owner_id,
        "server_id": server_id,
    }))
    return {"statusCode": 200, "body": "World save recorded"}

# Minecraft server status update trigger
def _handler_webhook_request(event: Dict[str, Any]) -> Dict[str, Any]:
    try:
        body: Dict[str, Any] = json.loads(event.get("body") or "{}")

    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON body"})

    server_id: Optional[str] = body.get("server_id")
    status: Optional[str] = body.get("status")
    playit_address: Optional[str] = body.get("playit_address")

    if not server_id or not status:
        logger.error(json.dumps({"event": "webhook_missing_fields", "body": body}))
        return _response(400, {"error": "server_id and status are required"})

    if status not in VALID_STATUSES:
        logger.error(json.dumps({
            "event": "webhook_invalid_status",
            "server_id": server_id,
            "status": status,
        }))
        return _response(400, {"error": f"status must be one of {sorted(VALID_STATUSES)}"})

    try:
        gsi_result = table.query(
            IndexName=GSI_NAME,
            KeyConditionExpression="server_id = :sid",
            ExpressionAttributeValues={":sid": server_id},
        )

    except ClientError as exc:
        logger.error(json.dumps({
            "event": "webhook_gsi_query_failed",
            "server_id": server_id,
            "error": str(exc),
        }))
        return _response(500, {"error": "Failed to resolve server"})

    items = gsi_result.get("Items", [])
    if not items:
        logger.warning(json.dumps({
            "event": "webhook_unknown_server_id",
            "server_id": server_id,
        }))
        return _response(404, {"error": "Server not found"})

    owner_id = items[0]["owner_id"]
    update_expr = "SET #s = :status, updated_at = :now"
    expr_names = {"#s": "status"} # "status" is a dynamodb reserved word
    expr_values: Dict[str, Any] = {
        ":status": status,
        ":now": datetime.now(timezone.utc).isoformat(),
    }

    if playit_address:
        update_expr += ", playit_address = :addr"
        expr_values[":addr"] = playit_address

    try:
        table.update_item(
            Key={"owner_id": owner_id, "server_id": server_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
        )

    except ClientError as exc:
        logger.error(json.dumps({
            "event": "webhook_update_failed",
            "owner_id": owner_id,
            "server_id": server_id,
            "status": status,
            "error": str(exc),
        }))
        return _response(500, {"error": "Failed to update server status"})

    logger.info(json.dumps({
        "event": "webhook_status_updated",
        "owner_id": owner_id,
        "server_id": server_id,
        "status": status,
        "playit_address_set": bool(playit_address),
    }))
    return _response(200, {"message": "Status updated"})

def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
