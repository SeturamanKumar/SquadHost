#!/bin/bash

if [ ! -f aws_credentials.env ]; then
    echo "ERROR: aws_credentials.env file not found!"
    exit 1
fi

echo "Executing Dockerized Deletion..."

docker run --rm -it \
    --env-file aws_credentials.env \
    -v "$(pwd)":/workspace \
    squadhost-deployer \
    /bin/bash -c "chmod +x kill_all.sh && ./kill_all.sh"