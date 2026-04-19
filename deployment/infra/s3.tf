resource "aws_s3_bucket" "images" {
  bucket = var.s3_bucket_images

  tags = { Project = "busstop" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "images_encryption" {
  bucket = aws_s3_bucket.images.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}
