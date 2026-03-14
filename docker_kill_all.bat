@echo off
cd /d "%~dp0"
if not exist aws_credentials.env (
    echo ERROR: aws_credentials.env file not found!
    exit /b 1 
)

echo Initialising Nuclear Teardown for SquadHost...
echo [CRITICAL] Do NOT close this window or press Ctril+C! Orphaned AWS resources will cost you money!
echo Executing Dockerized Deletion...

docker run --rm -it ^
    --env-file aws_credentials.env ^
    -v "%cd%":/workspace ^
    squadhost-deployer ^
    /bin/bash -c "dos2unix /workspace/kill_all.sh; chmod +x /workspace/kill_all.sh; cd /workspace; ./kill_all.sh"

echo Teardown complete. All AWS resources destroyed. Your bill is safe.