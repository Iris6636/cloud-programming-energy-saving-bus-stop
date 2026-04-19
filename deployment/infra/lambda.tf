resource "aws_lambda_function" "presence_to_v2" {
  function_name    = "busstop-PresenceTov2"
  filename         = "${path.module}/../lambda/PresenceTov2.zip"
  source_code_hash = filebase64sha256("${path.module}/../lambda/PresenceTov2.zip")
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.13"
  role             = aws_iam_role.lambda_exec.arn
  timeout          = 10

  tags = { Project = "busstop" }
}

resource "aws_lambda_function" "v2_base64_to_s3" {
  function_name    = "busstop-v2Base64toS3"
  filename         = "${path.module}/../lambda/v2Base64toS3.zip"
  source_code_hash = filebase64sha256("${path.module}/../lambda/v2Base64toS3.zip")
  handler          = "v2Base64toS3.lambda_handler"
  runtime          = "python3.13"
  role             = aws_iam_role.lambda_exec.arn
  timeout          = 10

  environment {
    variables = {
      S3_BUCKET_IMAGES = var.s3_bucket_images
    }
  }

  tags = { Project = "busstop" }
}
