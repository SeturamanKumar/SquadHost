import boto3
import os
import time
import psycopg2
import subprocess

DB_HOST = os.environ.get('RDS_HOSTNAME')
DB_NAME = os.environ.get('RDS_DB_NAME', 'postgres')
DB_USER = os.environ.get('RDS_USERNAME')
DB_PASS = os.environ.get('RDS_PASSWORD')
DB_URL = f"postgres://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"
STATE_BUCKET = os.environ.get('BACKUP_BUCKET_NAME')
REGION = os.environ.get('AWS_REGION', 'ap-south-1')

MAX_INACTIVITY = 3600
CHECK_INTERVAL = 300
inactive_timer = 0

ec2 = boto3.client('ec2', region_name=REGION)

def is_system_active():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM servers_minecraftserver WHERE status != 'OFFLINE';")
        db_active = cur.fetchone()[0] > 0
        cur.close()
        conn.close()
        if db_active: return True
    except Exception as e:
        print(f"DB checked failed: {e}")

    workers = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Name', 'Values': ['squadhost-worker-*']},
            {'Name': 'instance-state-name', 'Values': ['running', 'pending']}
        ]
    )
    return len(workers['Reservations']) > 0

while True:
    if is_system_active():
        inactive_timer = 0
    else:
        inactive_timer += CHECK_INTERVAL
        print(f"Idle: {inactive_timer}/{MAX_INACTIVITY}")

    if inactive_timer >= MAX_INACTIVITY:
        print("INITIATIING SOFT-TERMINATION BACKUP...")

        dump_cmd = f"PGPASSWORD='{DB_PASS}' pg_dump -h {DB_HOST} -U {DB_USER} -d {DB_NAME} > /tmp/db_restore.sql"
        subprocess.run(dump_cmd, shell=True)

        upload_cmd = f"aws s3 cp /tmp/db_restore.sql s3://{STATE_BUCKET}/backups/db_restore.sql"
        subprocess.run(upload_cmd, shell=True)

        os.chdir("/opt/SquadHost/infrastructure")
        subprocess.run([
            "terraform", "destroy",
            "-target=aws_db_instance.postgres",
            "-target=aws_instance.squadhost_server",
            "-auto-approve"
        ])
        break

    time.sleep(CHECK_INTERVAL)