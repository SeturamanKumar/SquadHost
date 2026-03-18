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
                "action": action,
                "mc_version": server.mc_version,
                "difficulty": server.difficulty,
                "max_players": server.max_players,
                "allow_tlauncher": server.allow_tlauncher,
                "seed": server.seed,
                "ram": server.ram,
            })
        }

        response = lambda_client.invoke(
            FunctionName='squadhost_create_server',
            InvocationType='Event',
            Payload=json.dumps(payload),
        )
        
        if response.get('StatusCode') != 202:
            logger.error(f"Lambda rejected the invocation {server.server_name}: {response}")
            return False, "Lambda failed to accept the request"
        
        if action == "START":
            server.refresh_from_db()
            server.is_running = True
            server.save()
        elif action == "STOP":
            server.refresh_from_db()
            server.is_running = False
            server.server_ip = None
            server.save()
        
        return True, f"Server {server.server_name} is being provisioned in the cloud"
    
    except MinecraftServer.DoesNotExist:
        return False, "Server not found in database"
    
    except Exception as e:
        logger.exception("orchastrator critical failure")
        return False, str(e)
