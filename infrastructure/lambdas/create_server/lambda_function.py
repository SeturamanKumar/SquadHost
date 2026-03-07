import boto3
import json
import base64
import os

def lambda_handler(event, context):
    region = os.environ.get('AWS_REGION', 'ap-south-1')
    ec2 = boto3.client('ec2', region_name=region)

    body = json.loads(event.get('body', '{}'))
    server_name = body.get('server_name', 'default-server')

    mc_version = body.get('mc_version', 'LATEST')
    difficulty = body.get('difficulty', 'normal')
    max_players = body.get('max_players', 10)
    allow_tlauncher = body.get('allow_tlauncher', False)
    seed = body.get('seed', '')

    s3_bucket = os.environ.get('S3_BACKUP_BUCKET')
    worker_ami_id = os.environ.get('WORKER_AMI_ID')

    sg_id = os.environ.get('SECURITY_GROUP_ID')
    subnet_id = os.environ.get('SUBNET_ID')

    online_mode = "FALSE" if allow_tlauncher else "TRUE"
    seed_env = f"-e SEED={seed} \\" if seed else "\\"

    user_data_script = f"""#!/bin/bash
apt-get update -y
apt-get install -y docker.io unzip zip curl

curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -q awscliv2.zip
./aws/install

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
    -e VERSION={mc_version} \\
    -e DIFFICULTY={difficulty} \\
    -e MAX_PLAYERS={max_players} \\
    -e ONLINE_MODE={online_mode} \\
    {seed_env}
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

    if [ $INACTIVE_MINUTES -ge 2 ]; then
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
            KeyName='squadhost-key',
            SecurityGroupIds=[sg_id],
            SubnetId=subnet_id,
            UserData=user_data_script,
            IamInstanceProfile={'Name': 'squadhost_worker_profile'},
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': f"squadhost-worker-{server_name}"}]
            }],
        )

        instance_id = response['Instances'][0]['InstanceId']

        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id], WaiterConfig={'Delay': 2, 'MaxAttempts': 30})

        instances = ec2.describe_instances(InstanceIds=[instance_id])
        public_ip = instances['Reservations'][0]['Instances'][0].get('PublicIpAddress')

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Provisioning Started',
                'ip': public_ip,
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({ 'error': str(e) })
        }