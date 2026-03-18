import boto3
import json
import os
import urllib.request

def lambda_handler(event, context):
    region = os.environ.get('AWS_REGION', 'ap-south-1')
    ec2 = boto3.client('ec2', region_name=region)

    body = json.loads(event.get('body', '{}'))
    server_name = body.get('server_name', 'default-server')
    action = body.get('action', 'START')

    if action == 'STOP':
        try:
            instances = ec2.describe_instances(
                Filters=[
                    {'Name': 'tag:Name', 'Values': [f"squadhost-worker-{server_name}"]},
                    {'Name': 'instance-state-name', 'Values': ['running', 'pending', 'stopping', 'stopped']},
                ]
            )
            instance_ids = [i['InstanceId'] for r in instances.get('Reservations', []) for i in r.get('Instances', [])]

            if instance_ids:
                ec2.terminate_instances(InstanceIds=instance_ids)
                return {'statusCode': 200, 'body': json.dumps({'message': 'Worker Terminated'})}
            return {'statusCode': 200, 'body': json.dumps({'message': 'No Worker Found'})}
        except Exception as e:
            return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}


    mc_version = body.get('mc_version', 'LATEST')
    difficulty = body.get('difficulty', 'normal')
    max_players = body.get('max_players', 10)
    allow_tlauncher = body.get('allow_tlauncher', False)
    seed = body.get('seed', '')
    ram = body.get('ram', 4)

    instance_type_map = {
        2: 't3.small',
        4: 't3.medium',
        8: 't3.large',
        16: 't3.xlarge',
    }
    instance_type = instance_type_map.get(ram, 't3.medium')
    memory_allocation = f"{ram*1024 - 512}M"

    s3_bucket = os.environ.get('S3_BACKUP_BUCKET')
    worker_ami_id = os.environ.get('WORKER_AMI_ID')
    sg_id = os.environ.get('SECURITY_GROUP_ID')
    subnet_id = os.environ.get('SUBNET_ID')

    online_mode = "FALSE" if allow_tlauncher else "TRUE"
    seed_env = f"-e SEED={seed} \\" if seed else "\\"

    django_api_url = os.environ.get('DJANGO_WEBHOOK_URL', '')
    webhook_secret = os.environ.get('WEBHOOK_SECRET', '')

    user_data_script = f"""#!/bin/bash
apt-get update -y
apt-get install -y unzip zip curl ca-certificates

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu noble stable" > /etc/apt/sources.list.d/docker.list
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io

curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -q awscliv2.zip
./aws/install

curl -s -X POST {django_api_url} \
    -H "Content-Type: application/json" \
    -d '{{"server_name": "{server_name}", "status": "INSTALLING", "webhook_secret": "{webhook_secret}"}}'

mkdir -p /minecraft/data
cd /minecraft

aws s3 cp s3://{s3_bucket}/{server_name}.zip world.zip || echo "No existing world found. Starting fresh"

if [ -f "world.zip" ]; then
    unzip world.zip -d /minecraft/data/
fi

curl -s -X POST {django_api_url} \
    -H "Content-Type: application/json" \
    -d '{{"server_name": "{server_name}", "status": "STARTING", "webhook_secret": "{webhook_secret}"}}'

docker run -d \\
    -e EULA=TRUE \\
    -e RCON_PASSWORD=kamikaze \\
    -e ENABLE_RCON=true \\
    -e MEMORY={memory_allocation} \\
    -e VERSION={mc_version} \\
    -e DIFFICULTY={difficulty} \\
    -e MAX_PLAYERS={max_players} \\
    -e ONLINE_MODE={online_mode} \\
    {seed_env}
    -p 25565:25565 \\
    -v /minecraft/data:/data \\
    --name {server_name} \\
    --restart unless-stopped \\
    itzg/minecraft-server

curl -s -X POST {django_api_url} \
    -H "Content-Type: application/json" \
    -d '{{"server_name": "{server_name}", "status": "BOOTING", "webhook_secret": "{webhook_secret}"}}'

cat << 'EOF' > /minecraft/kamikaze.sh
#!/bin/bash
INACTIVE_MINUTES=0

sleep 300

while true; do
    if docker ps --filter "name=^/{server_name}$" --filter "status=running" --format '{{{{.Name}}}}' | grep -q "{server_name}"; then
        RCON_OUTPUT=$(docker exec {server_name} rcon-cli --password kamikaze list 2>/dev/null)
        RCON_EXIT=$?

        if [ $RCON_EXIT -ne 0 ]; then
            echo "RCON check failed, skipping this interval"
        elif echo "$RCON_OUTPUT" | grep -q "There are 0"; then
            INACTIVE_MINUTES=$((INACTIVE_MINUTES + 1))
        else
            INACTIVE_MINUTES=0
        fi
    else
        INACTIVE_MINUTES=$((INACTIVE_MINUTES+1))
    fi

    if [ $INACTIVE_MINUTES -ge 8 ]; then
        docker stop {server_name}

        cd /minecraft/data
        zip -r ../world.zip * -x "*.zip"
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

sleep 30

curl -s -X POST {django_api_url} \
    -H "Content-Type: application/json" \
    -d '{{"server_name": "{server_name}", "status": "ONLINE", "webhook_secret": "{webhook_secret}"}}'
"""

    try:
        response = ec2.run_instances(
            ImageId=worker_ami_id,
            InstanceType=instance_type,
            MinCount=1,
            MaxCount=1,
            KeyName='squadhost-key',
            SecurityGroupIds=[sg_id],
            SubnetId=subnet_id,
            IamInstanceProfile={'Name': 'squadhost_worker_profile'},
            UserData=user_data_script,
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': f"squadhost-worker-{server_name}"}]
            }],
        )

        instance_id = response['Instances'][0]['InstanceId']

        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id], WaiterConfig={'Delay': 10, 'MaxAttempts': 30})

        instances = ec2.describe_instances(InstanceIds=[instance_id])
        public_ip = instances['Reservations'][0]['Instances'][0].get('PublicIpAddress')


        if django_api_url and webhook_secret:
            payload = json.dumps({
                'server_name': server_name,
                'ip_address': public_ip,
                'webhook_secret': webhook_secret,
            }).encode('utf-8')

            req = urllib.request.Request(
                django_api_url,
                data=payload,
                headers={'Content-Type': 'application/json'}
            )
            try:
                urllib.request.urlopen(req, timeout=10)
            except Exception as e:
                print(f"webhook failed: {e}")

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
