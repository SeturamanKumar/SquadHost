@echo off
if not exist aws_credentials.env (
    echo ERROR: aws_credentials.env file not found!
    echo Please copy aws_credentials.env.template, rename it to aws_credentials.env, and add your keys.
    exit /b 1
)

echo Starting SquadHost Deployment...
echo [WARNING] Do NOT close this window or press Ctrl+C! Corrupting Terraform costs Money!
echo The execution may taking upto 10-15 minutes is normal.

echo Building the SquadHost Deployer Image...
docker build -t squadhost-deployer -f Dockerfile.deploy .

echo Executing Dockerized Deployment...
docker run --rm -it ^
    --env-file aws_credentials.env ^
    -v "%cd%":/workspace ^
    squadhost-deployer ^
    /bin/bash -c "chmod +x spin_up.sh && ./spin_up.sh"

set /p MASTER_IP=<master_ip.txt

echo Deployment complete! Opening http://%MASTER_IP%:3000

start http://%MASTER_IP%:3000