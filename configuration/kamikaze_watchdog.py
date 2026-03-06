import boto3
import os
import time
import subprocess
import logging

MAX_INACTIVITY = 300
CHECK_INTERVAL = 60
AWS_REGION = os.environ.get('AWS_REGION', 'ap-south-1')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ec2 = boto3.client('ec2', region_name=AWS_REGION)
rds = boto3.client('rds', region_name=AWS_REGION)

def is_system_active():
    try:
        workers = ec2.describe_instances(
            Filters=[
                {'Name': 'tag:Name', 'Values': ['squadhost-worker-*']},
                {'Name': 'instance-state-name', 'Values': ['pending', 'running']}
            ]
        )

        worker_count = sum(len(r['Instances']) for r in workers['Reservations'])
        return worker_count > 0
    except Exception as e:
        logger.error(f"EC2 check failed: {e}")
        return True
    
def backup_database():
    try:
        host = os.environ.get('RDS_HOSTNAME', '').split(':')[0]
        user = os.environ.get('RDS_USERNAME')
        password = os.environ.get('RDS_PASSWORD')
        bucket = os.environ.get('BACKUP_BUCKET_NAME')
        db_name = os.environ.get('RDS_DB_NAME', 'postgres')

        os.environ['PGPASSWORD'] = password
        subprocess.run([
            'pg_dump',
            '-h', host,
            '-U', user,
            '-F', 'c',
            '-d', db_name,
            '-f', '/tmp/db_store.sql'
        ], check=True)

        s3 = boto3.client('s3')
        s3.upload_file('/tmp/db_restore.sql', bucket, 'backups/db_restore.sql')
        logger.info("Database backed up successfully")
    except Exception as e:
        logger.error(f"Backup Failed: {e}")

def self_destruct():
    try:
        logger.info("INITIATING SOFT-TERMINATION BACKUP")
        rds.delete_db_instance(
            DBInstanceIdentifier='squadhost-db',
            SkipFinalSnapshot=True
        )

        masters = ec2.describe_instances(
            Filters=[
                {'Name': 'tag:Name', 'Values': ['Squadhost-Kamikaze-Node']},
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )

        for res in masters['Reservations']:
            for inst in res['Instances']:
                ec2.terminate_instances(InstanceIds=[inst['InstanceId']])
    except Exception as e:
        logger.error(f"Self destruct failed: {e}")

if __name__ == "__main__":
    inactive_time = 0
    while True:
        time.sleep(CHECK_INTERVAL)
        if is_system_active():
            inactive_time = 0
        else:
            inactive_time += CHECK_INTERVAL
            logger.info(f"Idle: {inactive_time}/{MAX_INACTIVITY}")

        if inactive_time >= MAX_INACTIVITY:
            backup_database()
            self_destruct()