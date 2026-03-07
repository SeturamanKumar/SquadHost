import boto3
import json
import os
import logging
from .models import MinecraftServer

logger = logging.getLogger(__name__)

def orchestrate_server_action(server_id, action="START"):
    try:
        server = MinecraftServer.objects.get(id=server_id)

        lambda_client = boto3.client('lambda', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))

        payload = {
            "body": json.dumps({
                "server_name": server.server_name,
                "action": action
            })
        }

        response = lambda_client.invoke(
            FunctionName='squadhost_create_server',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload),
        )

        res_payload = json.loads(response['Payload'].read().decode('utf-8'))

        if response.get('FunctionError'):
            logger.error(f"Lambda Error for {server.server_name}: {res_payload}")
            return False, res_payload.get('errorMessage', 'Unknown Lambda Error')
        
        if res_payload.get('statusCode') != 200:
            logger.error(f"Lambda Logical Error for {server.server_name}: {res_payload}")
            return False, res_payload.get('body', 'Unkown AWS Logic Error')
        
        if action == "START":
            server.status = 'ONLINE'
        
            try:
                inner_body = json.loads(res_payload.get('body', '{}'))
                if inner_body.get('ip'):
                    server.server_ip = inner_body.get('ip')
            except json.JSONDecodeError:
                pass

            server.save()
        
        return True, f"Server {server.server_name} is being provisioned in the cloud"
    
    except MinecraftServer.DoesNotExist:
        return False, "Server not found in database"
    
    except Exception as e:
        logger.exception("orchastrator critical failure")
        return False, str(e)