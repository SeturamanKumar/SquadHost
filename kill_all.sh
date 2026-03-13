#!/bin/bash

echo "--------INITATING SQUADHOST NUCLEAR TEARDOWN--------"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR/infrastructure" || { echo "❌ Failed to find infrastructure directory"; exit 1; }

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$AWS_DEFAULT_REGION
STATE_BUCKET_NAME="squadhost-tfstate-${AWS_ACCOUNT_ID}"

echo "Step 0: Initialising Terraform with remote state..."
terraform init \
    -backend-config="bucket=$STATE_BUCKET_NAME" \
    -backend-config="key=terraform.tfstate" \
    -backend-config="region=${AWS_REGION}"

echo "Step 1: Destroying EC2, RDS, VPC and Backup S3 Bucket..."
terraform destroy -auto-approve


echo "Step 2: Locating Terraform State Bucket (${STATE_BUCKET_NAME})..."

if aws s3api head-bucket --bucket "$STATE_BUCKET_NAME" 2>/dev/null; then
    echo "Purging all versioned objects from state bucket..."
    python - <<PYEOF
import boto3
s3 = boto3.client('s3', region_name='${AWS_REGION}')
bucket = '${STATE_BUCKET_NAME}'

paginator = s3.get_paginator('list_object_versions')
for page in paginator.paginate(Bucket=bucket):
    versions = page.get('Versions', [])
    markers = page.get('DeleteMarkers', [])
    objects = [{'Key': o['Key'], 'VersionId': o['VersionId']} for o in versions + markers]
    if objects:
        s3.delete_objects(Bucket=bucket, Delete={'Objects': objects})

print("All versions purged")
PYEOF
    
    echo "Deleting the state bucket..."
    aws s3api delete-bucket --bucket "$STATE_BUCKET_NAME" --region "$AWS_REGION"
    echo "State bucket vaporized"
else
    echo "State bucket already deleted or does not exist. Skipping"
fi

echo "Step 3: Cleaning local workspace"
rm -rf .terraform
rm -f .terraform.lock.hcl

echo "Teardown complete. Your aws billing is now 0.00"