#!/bin/bash

echo "IGNITING SQUADHOST"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR/infrastructure" || { echo "Failed to Find infrastructure directory"; exit 1; }

echo "Step 1: Provisioning AWS infrastructure"
terraform init
terraform apply -auto-approve

echo "Step 2: Extracting connection details..."
SERVER_IP=$(terraform output -raw squadhost_server_ip)
DB_ENDPOINT=$(terraform output -raw rds_endpoint)
DB_USER=$(terraform output -raw db_username)
DB_PASS=$(terraform output -raw db_password)

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
    --extra-vars "rds_endpoint=$DB_ENDPOINT db_user=$DB_USER db_password=$DB_PASS"

echo "Squadhost is officially live! Access the dashboard at http://$SERVER_IP:3000"