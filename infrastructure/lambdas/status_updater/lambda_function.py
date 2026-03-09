import json
import os
import urllib.request
import urllib.parse

def lambda_handler(event, context):
    try:
        s3_record = event['Records'][0]['s3']
        file_key = urllib.parse.unquote_plus(s3_record['object']['key'])

        server_name = file_key.replace('.zip', '')

    except KeyError:
        return {'statusCode': 400, 'body': 'Invalid S3 Event structure'}
    
    django_api_url = os.environ.get('DJANGO_WEBHOOK_URL')
    webhook_secret = os.environ.get('WEBHOOK_SECRET')

    if not django_api_url:
        return {'statusCode': 500, 'body': 'Missing Django URL'}
    
    payload = json.dumps({
        'server_name': server_name,
        'status': 'OFFLINE',
        'webhook_secret': webhook_secret,
    }).encode('utf-8')

    req = urllib.request.Request(
        django_api_url,
        data=payload,
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = response.read().decode('utf-8')
            print(f"Successfully notified Django for {server_name}: {result}")
            return {'statusCode': 200, 'body': result}
    except Exception as e:
        print(f"Failed to notify Django: {str(e)}")
        return {'statusCode': 500, 'body': str(e)}