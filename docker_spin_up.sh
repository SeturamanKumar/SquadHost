#!/bin/bash

if [ ! -f aws_credentials.env ]; then
    echo "ERROR: aws_credentials.env file not found"
    echo "Please copy aws_credentials.env.template, rename it to aws_credentials.env, and add your keys."
    exit 1
fi

echo "Building the Squadhost Deployer Image..."
docker build -t squadhost-deployer -f Dockerfile.deploy .

echo "Executing Dockerized Deployment..."
docker run --rm -it \
    --env-file aws_credentials.env \
    -v "$(pwd)":/workspace \
    squadhost-deployer \
    /bin/bash -c "chmod +x spin_up.sh && ./spin_up.sh"