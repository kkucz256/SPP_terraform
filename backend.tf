terraform {
  backend "s3" {
    bucket         = "terraform-state-backend123456789"
    key            = "sensor-lambda/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-lock"
    encrypt        = true
  }
}
