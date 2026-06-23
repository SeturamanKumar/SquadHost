# Returns every Minecraft server owned by the authenticated user. Will be invoked by API Gateway behind a Cognito JWT authorizer
import json
import logging
import os
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

# Handle API Gateway request to list all servers owned by the caller. The caller should already be authorized by Cognito JWT.
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        owner_id = event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    except KeyError:
        logger.error(json.dumps({"event": "missing_jwt_claims"}))
        return _response(401, {"error": "Missing or invalid authentication"})

    try:
        result = table.query(
            KeyConditionExpression="owner_id = :owner_id",
            ExpressionAttributeValues={":owner_id": owner_id},
        )
    except ClientError as exc:
        logger.error(json.dumps({
            "event": "dynamodb_query_failed",
            "owner_id": owner_id,
            "error": str(exc),
        }))
        return _response(500, {"error": "Failed to retrieve servers"})

    servers = result.get("Items", [])
    logger.info(json.dumps({
        "event": "list_servers_success",
        "owner_id": owner_id,
        "count": len(servers),
    }))

    return _response(200, {"servers": servers})

# Compatible response for API Gateway.
def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:

    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, cld=DecimalEncoder),
    }
