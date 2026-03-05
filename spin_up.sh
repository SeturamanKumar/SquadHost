#!/bin/bash

echo "IGNITING SQUADHOST"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR/infrastructure" || { echo "Failed to Find infrastructure directory"; exit 1; }

echo "Step 0: Bootstrapping Terraform State Bucket..."

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
MASTER_REGION=$(aws configure get region)
STATE_BUCKET="squadhost-tfstate-${ACCOUNT_ID}"

if aws s3 ls "s3://$STATE_BUCKET" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "Creating remote state bucket: $STATE_BUCKET"
    aws s3 mb "s3://$STATE_BUCKET" --region "$MASTER_REGION"
else
    echo "Remote state bucket $STATE_BUCKET already exists"
fi

echo "Step 1: Provisioning AWS infrastructure"
terraform init -backend-config="bucket=$STATE_BUCKET"
terraform apply -auto-approve

echo "Step 2: Extracting connection details..."
SERVER_IP=$(terraform output -raw squadhost_server_ip)
DB_ENDPOINT=$(terraform output -raw rds_endpoint)
DB_USER=$(terraform output -raw db_username)
DB_PASS=$(terraform output -raw db_password)
WEBHOOK_SEC=$(terraform output -raw webhook_secret)

echo "Infrastructure built! EC2 server IP: $SERVER_IP"

echo "Waiting 45 seconds for the Ubuntu server to fully boot..."
sleep 45

cd "$SCRIPT_DIR"

echo "Step 3: Configuring the server via Ansible..."

export ANSIBLE_CONFIG="$SCRIPT_DIR/configuration/ansible.cfg"
export ANSIBLE_HOST_KEY_CHECKING=False

ansible-playbook -i "$SERVER_IP," "$SCRIPT_DIR/configuration/playbook.yml" \
    --private-key "$SCRIPT_DIR/infrastructure/squadhost-key.pem" \
    -u ubuntu \
    --extra-vars "rds_endpoint=$DB_ENDPOINT db_user=$DB_USER db_password=$DB_PASS webhook_secret=$WEBHOOK_SEC"

echo "Squadhost is officially live! Access the dashboard at http://$SERVER_IP:3000"