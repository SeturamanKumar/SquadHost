#!/bin/bash

if [ ! -f aws_credentials.env ]; then
    echo "ERROR: aws_credentials.env file not found"
    echo "Please copy aws_credentials.env.template, rename it to aws_credentials.env, and add your keys."
    exit 1
fi

trap 'echo -e "\n[WARNING] Please wait! Interrupting Terraform will corrupt some files and cost you money!"' SIGINT
echo "Starting Squadhost Deployment..."
echo "The execution taking upto 10-15 minutes is normal"

echo "Building the Squadhost Deployer Image..."
docker build -t squadhost-deployer -f Dockerfile.deploy .

echo "Executing Dockerized Deployment..."
docker run --rm -it \
    --env-file aws_credentials.env \
    -v "$(pwd)":/workspace \
    squadhost-deployer \
    /bin/bash -c "chmod +x spin_up.sh && ./spin_up.sh"

MASTER_IP=$(cat ./master_ip.txt)

echo "Deployment complete! Opening http://$MASTER_IP:3000"

if [[ "$OSTYPE" == "darwin"* ]]; then
    open "http://$MASTER_IP:3000"
else
    xdg-open "http://$MASTER_IP:3000"
fi

trap - SIGINT