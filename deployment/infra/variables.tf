variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "s3_bucket_images" {
  description = "S3 bucket name for storing bus stop photos (must be globally unique)"
  type        = string
  default     = "busstop-images-temp"
}
