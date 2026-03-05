import boto3
import json
import base64
import os

def lambda_handler(event, context):
    ec2 = boto3.client('ec2', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))

    body = json.loads(event.get('body', '{}'))
    server_name = body.get('server_name', 'default-server')
    s3_bucekt = os.environ.get('S3_BACKUP_BUCKET')

    user_data_script = f"""#!/bin/bash
    apt-get update -y
    apt-get install -y docker.io awscli unzip

    mkdir -p /minecraft/data
    cd /minecraft

    aws s3 cp s3://{s3_bucekt}/{server_name}.zip world.zip || echo "No existing world found. Starting fresh"

    if [-f "world.zip"]; then
        unzip world.zip -d /minecraft/data/
    fi

    docker run -d \\
        -e EULA=TRUE \\
        -p 25565:25565 \\
        -v /minecraft/data:/data \\
        --name {server_name} \\
        --restart unless-stopped \\
        itzg/minecraft-server
    """

    try:
        response = ec2.run_instances(
            ImageId='ami-03f4878755434977f',
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