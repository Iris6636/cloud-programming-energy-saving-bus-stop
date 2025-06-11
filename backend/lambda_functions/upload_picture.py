import json
import base64, boto3

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    file_data = base64.b64decode(event['image_data'])  # 從 MQTT message 中取得
    s3.put_object(Bucket='your-bucket-name', Key='photo.jpg', Body=file_data)


def lambda_handler(event, context):
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
