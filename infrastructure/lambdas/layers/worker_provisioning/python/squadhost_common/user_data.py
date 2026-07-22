# Shared logic for creating or restarting Minecraft servers. Includes
# Instance types based on ram input
# Ram allotment for the docker container
# SigV4 Helper
# create the Miencraft server EC2

from typing import Dict

INSTANCE_TYPE_MAP: Dict[int, str] = {
    2: "t3a.small",
    4: "t3a.medium",
    8: "t3a.large",
    16: "t3a.xlarge",
}

MEMORY_MB_MAP: Dict[int, int] = {
    2: 1024,
    4: 2688,
    8: 6144,
    16: 13312,
}

# SigV4 signing helper
_SIGV4_SCRIPT = """\
import hashlib
import hmac
import json
import sys
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlparse

def _fetch_credentials():

    token_req = urllib.request.Request(
        "http://169.254.169.254/latest/api/token",
        method="PUT",
        headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
    )

    with urllib.request.urlopen(token_req, timeout=5) as r:
        imds_token = r.read().decode().strip()

    role_req = urllib.request.Request(
        "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
        headers={"X-aws-ec2-metadata-token": imds_token},
    )

    with urllib.request.urlopen(role_req, timeout=5) as r:
        role_name = r.read().decode().strip()

    creds_req = urllib.request.Request(
        f"http://169.254.169.254/latest/meta-data/iam/security-credentials/{role_name}",
        headers={"X-aws-ec2-metadata-token": imds_token},
    )

    with urllib.request.urlopen(creds_req, timeout=5) as r:
        return json.loads(r.read().decode())

def _hmac_sha256(key, msg):

    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

def _signing_key(secret_key, date, region, service):

    # SigV4 key derivation chain:
    # kDate    = HMAC("AWS4" + kSecret, Date)
    # kRegion  = HMAC(kDate, Region)
    # kService = HMAC(kRegion, Service)
    # kSigning = HMAC(kService, "aws4_request")
    k = _hmac_sha256(f"AWS4{secret_key}".encode("utf-8"), date)
    k = _hmac_sha256(k, region)
    k = _hmac_sha256(k, service)
    return _hmac_sha256(k, "aws4_request")

def signed_post(url, payload, region):

    creds = _fetch_credentials()
    now = datetime.now(timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")

    parsed = urlparse(url)
    host = parsed.netloc
    uri = parsed.path or "/"
    payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    canonical_headers = (
        f"content-type:application/json\\n"
        f"host:{host}\\n"
        f"x-amz-date:{amz_date}\\n"
        f"x-amz-security-token:{creds['Token']}\\n"
    )
    signed_headers = "content-type;host;x-amz-date;x-amz-security-token"

    canonical_request = "\\n".join([
        "POST",
        uri,
        "",
        canonical_headers,
        signed_headers,
        payload_hash,
    ])

    scope = f"{date_stamp}/{region}/execute-api/aws4-request"
    string_to_sign = "\\n".join([
        "AWS4-HMAC-SHA256",
        amz_date,
        scope,
        hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
    ])

    sig = hmac.new(
        _signing_key(creds["SecretAccessKey"], date_stamp, region, "execute-api"),
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    auth = (
        f"AWS4-HMAC-SHA256 Credential={creds['AccessKeyId']}/{scope},"
        f"SignedHeaders={signed_headers}, Signature={sig}"
    )

    req = urllib.request.Request(
        url,
        data=payload.encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Amz-Date": amz_date,
            "X-Amz-Security-Token": creds["Token"],
            "Authorization": auth,
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            print(f"[sigv4] POST {url} -> {r.status}", flush=True)
            return r.status

    except urllib.error.HTTPError as exc:
        print(f"[sigv4] HTTP {exc.code}: {exc.reason}", flush=True)
        return exc.code

    except Exception as exc:
        print(f"[sigv4] request failed: {exc}", flush=True)
        return 500

if __name__ == "__main__":

    if len(sys.argv) != 4:
        print("Usage: sigv4_request.py <URL> <JSON_PAYLAOD> <REGION>", file=sys.stderr)
        sys.exit(1)

    _, url, payload, region = sys.argv
    sys.exit(0 if signed_post(url, payload, region) < 400 else 1)

"""

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
    ram_tier: int,
    s3_bucket: str,
    s3_world_key: str,
    webhook_url: str,
    region: str,
    playitgg_secret_name: str,
) -> str:

    memory_mb = MEMORY_MB_MAP[ram_tier]
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
chmod +x /opt/sigv4_request.py

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

apt-get update -y
apt-get install -y unzip zip curl ca-certificates

# Docker installation
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

curl -fsSL https://playit.gg/downloads/playit-linux-amd64 -o /usr/local/bin/playit
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
