import boto3
import json
import base64
import os

def lambda_handler(event, context):
    region = os.environ.get('AWS_REGION', 'ap-south-1')
    ec2 = boto3.client('ec2', region_name=region)

    body = json.loads(event.get('body', '{}'))
    server_name = body.get('server_name', 'default-server')
    s3_bucket = os.environ.get('S3_BACKUP_BUCKET')
    worker_ami_id = os.environ.get('WORKER_AMI_ID')

    user_data_script = f"""#!/bin/bash
    apt-get update -y
    apt-get install -y docker.io awscli unzip zip

    mkdir -p /minecraft/data
    cd /minecraft

    aws s3 cp s3://{s3_bucket}/{server_name}.zip world.zip || echo "No existing world found. Starting fresh"

    if [ -f "world.zip" ]; then
        unzip world.zip -d /minecraft/data/
    fi

    docker run -d \\
        -e EULA=TRUE \\
        -e RCON_PASSWORD=kamikaze \\
        -e ENABLE_RCON=true \\
        -p 25565:25565 \\
        -p 25575:25575 \\
        -v /minecraft/data:/data \\
        --name {server_name} \\
        --restart unless-stopped \\
        itzg/minecraft-server

    cat << 'EOF' > /minecraft/kamikaze.sh
    #!/bin/bash
    INACTIVE_MINUTES=0

    sleep 300

    while true; do
        PLAYERS=$(docker exec {server_name} rcon-cli --password kamikaze list | grep -o 'There are 0')

        if [ ! -z "$PLAYERS" ]; then
            INACTIVE_MINUTES=$((INACTIVE_MINUTES + 1))
        else
            INACTIVE_MINUTES=0
        fi

        if [ $INACTIVE_MINUTES -ge 5 ]; then
            docker stop {server_name}

            cd /minecraft/data
            zip -r ../world.zip *
            aws s3 cp ../world.zip s3://{s3_bucket}/{server_name}.zip
            TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
            INSTANCE_ID=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/instance-id)

            aws ec2 terminate-instances --instance-ids $INSTANCE_ID --region {region}
            break
        fi

        sleep 60
    
    done
    EOF

    chmod +x /minecraft/kamikaze.sh
    nohup /minecraft/kamikaze.sh > /minecraft/kamikaze.log 2>&1 &
    """

    try:
        response = ec2.run_instances(
            ImageId=worker_ami_id,
            InstanceType='t3.small',
            MinCount=1,
            MaxCount=1,
            UserData=user_data_script,
            IamInstanceProfile={'Name': 'squadhost_worker_profile'},
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': f"squadhost-worker-{server_name}"}]
            }],
        )

        instance_id = response['Instances'][0]['InstanceId']

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Minecraft Worker Node provisioning started',
                'instance_id': instance_id,
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({ 'error': str(e) })
        }