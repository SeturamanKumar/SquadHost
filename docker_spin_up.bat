@echo off
if not exist aws_credentials.env (
    echo ERROR: aws_credentials.env file not found!
    echo Please copy aws_credentials.env.template, rename it to aws_credentials.env, and add your keys.
    exit /b 1
)

echo Building the SqaudHost Deployer Image...
docker build -t squadhost-deployer -f Dockerfile.deploy .

echo Executing Dockerized Deployment...
docker run --rm -it ^
    -env-file aws_credentials.env ^
    -v "%cd%":/workspace ^
    squadhost-deployer ^
    /bin/bash -c "chmod +x spin_up.sh && ./spin_up.sh"