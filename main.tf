provider "aws" {
  region                   = "us-east-1"
  shared_credentials_files = ["~/.aws/credentials"]
}

provider "archive" {}

data "aws_iam_role" "main_role" {
  name = "LabRole"
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda/handler.py"
  output_path = "${path.module}/lambda.zip"
}

resource "aws_dynamodb_table" "sensor_failures" {
  name         = "SensorFailuresTF"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "sensor_id"

  attribute {
    name = "sensor_id"
    type = "N"
  }
}


resource "aws_lambda_function" "sensor_handler" {
  function_name = "sensor_temperature_handler"
  role          = data.aws_iam_role.main_role.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
}