#!/bin/bash

if [ ! -f aws_credentials.env ]; then
    echo "ERROR: aws_credentials.env file not found!"
    exit 1
fi

echo "Executing Dockerized Deletion..."

read -p "Enter your AWS Access Key ID: " AWS_ACCESS_KEY_ID
read -s -p "Enter your AWS Secret Access Key: " AWS_SECRET_ACCESS_KEY
echo ""
read -p "Enter your AWS Region (e.g., ap-south-1): " AWS_DEFAULT_REGION

docker run --rm -it \
    --env-file aws_credentials.env \
    -v "$(pwd)":/workspace \
    squadhost-deployer \
    /bin/bash -c "chmod +x kill_all.sh && ./kill_all.sh"