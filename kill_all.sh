#!/bin/bash

echo "--------INITATING SQUADHOST NUCLEAR TEARDOWN--------"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR/infrastructure" || { echo "❌ Failed to find infrastructure directory"; exit 1; }

echo "Step 1: Destroying EC2, RDS, VPC and Backup S3 Bucket..."
terraform destroy -auto-approve

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configureget region)
STATE_BUCKET_NAME="squadhost-tf-state-${AWS_ACCOUNT_ID}"

echo "Step 2: Locating Terraform State Bucket (${STATE_BUCKET_NAME})..."

if aws s3api head-bucket --bucket "$STATE_BUCKET_NAME" 2>/dev/null; then
    echo "Emptying the state bucket..."
    aws s3 rm "s3://${STATE_BUCKET_NAME}" --recursive

    echo "Deleting the state bucket..."
    aws s3api delete-bucket --bucket "$STATE_BUCKET_NAME" --region "$AWS_REGION"
    echo "State bucket vaporized"
else
    echo "State bucket already deleted or does not exist. Skipping"
fi

echo "Step 3: Cleaning local workspace"
rm -rf .terraform
rm -f .terrafrom.lock.hcl

echo "Teardown complete. Your aws billing is now 0.00"