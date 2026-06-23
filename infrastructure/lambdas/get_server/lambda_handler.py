# Returns a single Minecraft server.
import json
import os
import logging
from decimal import Decimal
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ["SERVERS_TABLE"]
table = dynamodb.Table(TABLE_NAME)

# Converts DynamoDB decimal values to int/float
class DecimalEncoder(json.JSONEncoder):

    def default(self, obj: Any) -> Any:

        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().defualt(obj)

# Handle API Gateway request to list one server owned by the caller. The caller should already be authorized by Cognito JWT.
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:

    try:
        owner_id = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    except KeyError:
        logger.error(json.dumps({"event": "missing_jwt_claims"}))
        return _response(401, {"error": "Missing or invalid authentication"})

    try:
        server_id = event["pathParameters"]["id"]
    except:
        logger.error(json.dumps({"event": "missing_path_parameter", "owner_id": owner_id}))
        return _response(400, {"error": "Missing server id in request path"})

    try:
        result = table.get_item(Key={"owner_id": owner_id, "server_id": server_id})
    except ClientError as exc:
        logger.error(json.dumps({
            "event": "dynamodb_get_item_failed",
            "owner_id": owner_id,
            "server_id": server_id,
            "error": str(exc),
        }))
        return _response(500, {"error": "Failed to retrieve server"})

    item = result.get("Item")

    if item is None:
        logger.info(json.dumps({
            "event": "get_server_not_found",
            "owner_id": owner_id,
            "server_id": server_id,
        }))
        return _response(404, {"error": "Server not found"})

    logger.info(json.dumps({
        "event": "get_server_success",
        "owner_id": owner_id,
        "server_id": server_id,
    }))

    return _response(200, item)

# Compatible response for API Gateway.
def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:

    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, cld=DecimalEncoder),
    }
