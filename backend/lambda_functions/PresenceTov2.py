import boto3
import json

def lambda_handler(event, context):
    print("📥 接收到 presence=true 事件：", json.dumps(event))

    iot = boto3.client('iot-data', region_name='us-east-1')

    # 發送 MQTT 指令給 Raspberry Pi
    command = {
        "action": "take_picture"
    }

    iot.publish(
        topic="my/subscribetopic",
        qos=1,
        payload=json.dumps(command)
    )

    return {
        'statusCode': 200,
        'body': 'Picture command sent'
    }