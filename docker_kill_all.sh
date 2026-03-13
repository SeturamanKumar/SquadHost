#!/bin/bash

if [ ! -f aws_credentials.env ]; then
    echo "ERROR: aws_credentials.env file not found!"
    exit 1
fi

trap 'echo -e "\n[CRITICAL] Teardow in progress! Do no interrupt, or you will pay for orphaned AWS resources!"' SIGINT
echo "Initialising Nuclear Teardown for SquadHost..."

echo "Executing Dockerized Deletion..."

docker run --rm -it \
    --env-file aws_credentials.env \
    -v "$(pwd)":/workspace \
    squadhost-deployer \
    /bin/bash -c "chmod +x kill_all.sh && ./kill_all.sh"

echo "Teardown complete. All AWS resources destroyed. Your bill is safe."

trap - SIGINT