@echo off
if not exist aws_credentials.env (
    echo ERROR: aws_credentials.env file not found!
    exit \b 1 
)

echo Executing Dockerized Deletion...

docker run --rm -it ^
    -env_file aws_credentials.env ^
    -v "%cd":/workspace ^
    squadhost-deployer ^
    /bin/bash -c "chmod +x kill_all.sh && ./kill_all.sh"