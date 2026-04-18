output "iot_endpoint" {
  description = "IoT Core data endpoint (update this in iot/main.py)"
  value       = data.aws_iot_endpoint.current.endpoint_address
}

output "iot_thing_name" {
  description = "IoT Thing name"
  value       = aws_iot_thing.busstop.name
}

output "s3_bucket_images" {
  description = "S3 bucket name for bus stop photos"
  value       = aws_s3_bucket.images.bucket
}
