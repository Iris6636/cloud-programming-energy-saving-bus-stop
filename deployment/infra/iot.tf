data "aws_iot_endpoint" "current" {
  endpoint_type = "iot:Data-ATS"
}

resource "aws_iot_thing" "busstop" {
  name = "MyThing-113065528"
}

# Rule 1: Shadow presence false→true → PresenceTov2
resource "aws_iot_topic_rule" "presence_detected" {
  name        = "busstop_PresenceDetected"
  description = "Trigger PresenceTov2 Lambda when presence transitions false to true"
  enabled     = true
  sql         = "SELECT * FROM '$aws/things/MyThing-113065528/shadow/update/documents' WHERE current.state.reported.presence = true AND previous.state.reported.presence = false"
  sql_version = "2016-03-23"

  lambda {
    function_arn = aws_lambda_function.presence_to_v2.arn
  }

  tags = { Project = "busstop" }
}

# Rule 2: device/camera/image → v2Base64toS3
resource "aws_iot_topic_rule" "capture_image" {
  name        = "busstop_CaptureImageToS3"
  description = "Upload base64 camera image to S3"
  enabled     = true
  sql         = "SELECT * FROM 'device/camera/image'"
  sql_version = "2015-10-08"

  lambda {
    function_arn = aws_lambda_function.v2_base64_to_s3.arn
  }

  tags = { Project = "busstop" }
}

# Lambda permissions for IoT rules
resource "aws_lambda_permission" "iot_presence_detected" {
  statement_id  = "AllowIoTInvoke-PresenceDetected"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.presence_to_v2.function_name
  principal     = "iot.amazonaws.com"
  source_arn    = aws_iot_topic_rule.presence_detected.arn
}

resource "aws_lambda_permission" "iot_capture_image" {
  statement_id  = "AllowIoTInvoke-CaptureImage"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.v2_base64_to_s3.function_name
  principal     = "iot.amazonaws.com"
  source_arn    = aws_iot_topic_rule.capture_image.arn
}

# IoT Device Policy
resource "aws_iot_policy" "busstop_device_policy" {
  name = "busstop-DevicePolicy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "iot:Connect"
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = ["iot:Publish", "iot:Receive"]
        Resource = "arn:aws:iot:${var.aws_region}:${data.aws_caller_identity.current.account_id}:topic/*"
      },
      {
        Effect   = "Allow"
        Action   = "iot:Subscribe"
        Resource = "arn:aws:iot:${var.aws_region}:${data.aws_caller_identity.current.account_id}:topicfilter/*"
      },
      {
        Effect = "Allow"
        Action = ["iot:UpdateThingShadow", "iot:GetThingShadow"]
        Resource = "arn:aws:iot:${var.aws_region}:${data.aws_caller_identity.current.account_id}:thing/MyThing-113065528"
      }
    ]
  })
}
