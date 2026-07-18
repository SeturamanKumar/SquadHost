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
        "event": "create_server_success",
        "owner_id": owner_id,
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

# runs on the Worker instance to start Minecraft itzg docker image, start playitgg tunnel
# Fetches worlds from S3, updates DB status
def _build_user_data(
    owner_id: str,
    server_id: str,
    mc_version: str,
    difficulty: str,
    max_players: str,
    online_mode: str,
    seed: str,
    memory_mb: int,
    s3_bucket: str,
    s3_world_key: str,
    webhook_url: str,
    region: str,
    playitgg_secret_name: str,
) -> str:

    seed_env_flag = f"-e SEED={seed}" if seed else ""

    return f"""\
#!/bin/bash
set -euo pipefail
exec > >(tee /var/log/squadhost-init.log | logger -t squadhost-init) 2>&1

SERVER_ID="{server_id}"
OWNER_ID="{owner_id}"
S3_BUCKET="{s3_bucket}"
S3_WORLD_KEY="{s3_world_key}"
WEBHOOK_URL="{webhook_url}"
REGION="{region}"
MC_VERSION="{mc_version}"
DIFFICULTY="{difficulty}"
MAX_PLAYERS="{max_players}"
ONLINE_MODE="{online_mode}"
MEMORY_MB="{memory_mb}"
SEED="{seed}"
PLAYITGG_SECRET_NAME="{playitgg_secret_name}"
SEED_ENV_FLAG="{seed_env_flag}"

# SigV4 request helper
cat << 'SIGV4_EOF' > /opt/sigv4_request.py
{_SIGV4_SCRIPT}
SIGV4_EOF

# Status update helpers
send_status() {{
    local STATUS=$1
    local PAYLOAD
    PAYLOAD=$(printf '{{"server_id": "%s", "status": "%s"}}' "$SERVER_ID" "$STATUS")
    python3 /opt/sigv4_request.py "$WEBHOOK_URL" "$PAYLOAD" "$REGION" || true
}}

send_status_online() {{
    local STATUS=$1
    local ADDRESS=$2
    local PAYLOAD
    PAYLOAD=$(printf '{{"server_id": "%s", "status": "%s", "playit_address": "%s"}}' "$SERVER_ID" "$STATUS" "$ADDRESS")
    python3 /opt/sigv4_request.py "$WEBHOOK_URL" "$PAYLOAD" "$REGION" || true
}}

# Docker installation
apt-get update -y
apt-get install -y unzip zip curl ca-certificates

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu noble stable" > /etc/apt/sources.list.d/docker.list
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io

# AWS cli v2 installation
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
unzip -q /tmp/awscliv2.zip -d /tmp/awscli
/tmp/awscli/aws/install
rm -rf /tmp/awscli /tmp/awscliv2.zip

send_status "INSTALLING"

# Pull world from S3 if it exists
mkdir -p /minecraft/data
cd /minecraft

if aws s3 cp "s3://$S3_BUCKET/$S3_WORLD_KEY" /minecraft/world.zip --region "$REGION" 2>/dev/null; then
    echo "World found in S3, restoring..."
    unzip -q /minecraft/world.zip -d /minecraft/data/
    rm /minecraft/world.zip
else
    echo "No existing world in S3, starting fresh..."
fi

# Configure the playitgg tunnel
PLAYITGG_TOKEN=$(aws secretsmanager get-secret-value) \
    --secret-id "$PLAYITGG_SECRET_NAME" \
    --region "$REGION" \
    --query SecretString \
    --output text)

curl -fsSL https://playit.gg/downloads/playtit-linux-amd64 -o /usr/local/bin/playit
chmod +x /usr/local/bin/playit

mkdir -p /etc/playit
printf 'secret_key = "%s"\n' "$PLAYITGG_TOKEN" > /etc/playit/config.toml

nohup /usr/local/bin/playit --config /etc/playit/config.toml > /var/log/playit.log 2>&1 & 

PLAYIT_ADDRESS=""
for i in $(seq 1 30); do
    sleep 2
    PLAYIT_ADDRESS=$(grep -oP 'address: \K\S+' /var/log/playit.log 2>/dev/null | head -1 || true)
    if [ -n "$PLAYIT_ADDRESS" ]; then
        echo "playit.gg address: $PLAYIT_ADDRESS"
        break
    fi
done

send_status "STARTING"

# Generate RCON password for Minecraft server
RCON_PASSWORD=$(openssl rand -hex 16)

# Runtime configs for the Minecraft server
mkdir -p /minecraft
cat << EOF > /minecraft/server.env
SERVER_ID=$SERVER_ID
S3_BUCKET=$S3_BUCKET
S3_WORLD_KEY=$S3_WORLD_KEY
WEBHOOK_URL=$WEBHOOK_URL
REGION=$REGION
RCON_PASSWORD=$RCON_PASSWORD
EOF
chmod 600 /minecraft/server.env

# Run Minecraft container, container name will be server_id since for uniqueness
docker run -d \
    -e EULA=TRUE \
    -e RCON_PASSWORD="$RCON_PASSWORD" \
    -e ENABLE_RCON=true \
    -e MEMORY="${{MEMORY_MB}}M" \
    -e VERSION="$MC_VERSION" \
    -e DIFFICULTY="$DIFFICULTY" \
    -e MAX_PLAYERS="$MAX_PLAYERS" \
    -e ONLINE_MODE="$ONLINE_MODE" \
    $SEED_ENV_FLAG \
    -p 25565:25565 \
    -v /minecraft/data:/data \
    --name "$SERVER_ID" \
    --restart unless-stopped \
    itzg/minecraft-server

send_status "BOOTING"

# Stops the Minecraft server after 0 player activity for more than 6 minutes, Zips the world and saves it to S3 and updates server status
cat << 'KAMIKAZE_EOF' > /minecraft/kamikaze.sh
#!/bin/bash
set -euo pipefail
source /minecraft/server.env

INACTIVE_MINUTES=0
CONTAINER=$SERVER_ID

sleep 300

while true; do
    if docker ps --filter "name=$CONTAINER" --filter "status=running" | grep -q "$CONTAINER"; then
        RCON_OUTPUT=$(docker exec "$CONTAINER" rcon-cli --password "$RCON_PASSWORD" list 2>/dev/null || echo "RCON_FAILED")

        if echo "$RCON_OUTPUT" | grep -q "RCON_FAILED"; then
            echo "RCON check failed, skipping interval"
        elif echo "$RCON_OUTPUT" | grep -q "There are 0"; then
            INACTIVE_MINUTES=$((INACTIVE_MINUTES + 1))
        else
            INACTIVE_MINUTES=0
        fi

    else
        INACTIVE_MINUTES=$((INACTIVE_MINUTES + 1))
    fi

    if [ "$INACTIVE_MINUTES" -ge 6 ]; then
        # Update status to stopping
        PAYLOAD=$(printf '{"server_id": "%s", "status": "STOPPING"}' "$SERVER_ID")
        python3 /opt/sigv4_request.py "$WEBHOOK_URL" "$PAYLOAD" "$REGION" || true

        docker stop "$CONTAINER" || true

        # Zip the world and push to S3
        cd /minecraft/data
        zip -r /minecraft/world.zip . -x "*.zip"
        aws s3 cp /minecraft/world.zip "s3://$S3_BUCKET/$S3_WORLD_KEY" --region "$REGION"

        # Update status to offline
        PAYLOAD=$(printf '{"server_id": "%s", "status": "OFFLINE"}' "$SERVER_ID")
        python3 /opt/sigv4_request.py "$WEBHOOK_URL" "$PAYLOAD" "$REGION" || true

        # self-terminate using IMDSv2
        IMDS_TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
        INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $IMDS_TOKEN" "http://169.254.169.254/latest/meta-data/instance-id")

        aws ec2 terminate-instances --instance-ids "$INSTANCE_ID" --region "$REGION"
        break
    fi

    sleep 60
done
KAMIKAZE_EOF

chmod +x /minecraft/kamikaze.sh
nohup /minecraft/kamikaze.sh > /minecraft/kamkikaze.log 2>&1 &

# Update status to online
sleep 30
if [ -n "PLAYIT_ADDRESS" ]; then
    send_status_online "ONLINE" "$PLAYIT_ADDRESS"
else
    send_status "ONLINE"
fi

"""

def _response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
