import boto3
import base64
import json

def lambda_handler(event, context):
    print("📥 Received MQTT event:", json.dumps(event))

    # 從 event 中取得檔名與 base64 圖片資料
    filename = event["filename"]
    image_data_b64 = event["image_data"]

    # 解碼 base64 成為位元資料
    try:
        image_data = base64.b64decode(image_data_b64)
    except Exception as e:
        print("❌ Failed to decode base64:", e)
        return {"statusCode": 400, "body": "Invalid base64"}

    # 上傳到 S3
    s3 = boto3.client("s3")
    try:
        s3.put_object(
            Bucket="v2-pic",  
            Key=f"photos/{filename}",
            Body=image_data,
            ContentType="image/jpeg"
        )
        print(f"✅ Uploaded {filename} to S3")
    except Exception as e:
        print("❌ S3 upload failed:", e)
        return {"statusCode": 500, "body": "S3 upload failed"}

    return {"statusCode": 200, "body": f"Uploaded {filename}"}
