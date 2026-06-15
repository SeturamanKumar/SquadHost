# For Ubuntu AMI image
data "aws_ami" "ubuntu" {

  most_recent = true
  owners      = ["099720109477"]

  filter {

    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]

  }

  filter {

    name   = "virtualization-type"
    values = ["hvm"]

  }

}

# Generate SSH key pair and save to squadhost-key.pem
resource "tls_private_key" "squadhost_ssh_key" {

  algorithm = "RSA"
  rsa_bits  = 4096

}

resource "aws_key_pair" "squadhost_key_pair" {

  key_name   = "squadhost-key"
  public_key = tls_private_key.squadhost_ssh_key.public_key_openssh

  tags = {

    Name       = "squadhost-key-pair"
    project    = "squadhost"
    managed_by = "terraform"

  }

}

# Save the SSH key locally
resource "local_file" "squadhost_private_key" {

  content         = tls_private_key.squadhost_ssh_key.private_key_pem
  filename        = "${path.module}/squadhost-key.pem"
  file_permission = "0600"

}

# Start master EC2 instance and configures processes, Django and frontend
resource "aws_instance" "squadhost_server" {

  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t3.micro"
  subnet_id                   = aws_subnet.public_1.id
  vpc_security_group_ids      = [aws_security_group.ec2_sg.id]
  iam_instance_profile        = aws_iam_instance_profile.ec2_profile.name
  associate_public_ip_address = true
  key_name                    = aws_key_pair.squadhost_key_pair.key_name

  tags = {

    Name       = "squadhost-kamikaze-node"
    project    = "squadhost"
    managed_by = "terraform"

  }

}

# Webhook secret
resource "random_password" "webhook_secret" {

  length  = 32
  special = false

}

# create zip of lambda function
data "archive_file" "create_server_zip" {

  type        = "zip"
  source_dir  = "${path.module}/lambdas/create_server"
  output_path = "${path.module}/lambdas/create_server.zip"

}

# Create server lambda function
resource "aws_lambda_function" "create_server_lambda" {

  filename         = data.archive_file.create_server_zip.output_path
  function_name    = "squadhost_create_server"
  role             = aws_iam_role.lambda_ec2_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.create_server_zip.output_base64sha256
  timeout          = 300

  environment {

    variables = {

      S3_BACKUP_BUCKET   = aws_s3_bucket.squadhost_backups.bucket
      WORKER_AMI_ID      = data.aws_ami.ubuntu.id
      SECURITY_GROUP_ID  = aws_security_group.ec2_sg.id
      SUBNET_ID          = aws_subnet.public_1.id
      DJANGO_WEBHOOK_URL = "http://${aws_instance.squadhost_server.public_ip}:8000/api/servers/webhook/status"
      WEBHOOK_SECRET     = random_password.webhook_secret.result

    }

  }

  tags = {

    Name       = "squadhost-create-server"
    project    = "squadhost"
    managed_by = "terraform"

  }

}

# create zip of lambda function
data "archive_file" "status_updater_zip" {

  type        = "zip"
  source_dir  = "${path.module}/lambdas/status_updater"
  output_path = "${path.module}/lambdas/status_updater.zip"

}

# Create server lambda function
resource "aws_lambda_function" "status_updater_lambda" {

  filename         = data.archive_file.status_updater_zip.output_path
  function_name    = "squadhost_status_updater"
  role             = aws_iam_role.lambda_s3_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.status_updater_zip.output_base64sha256
  timeout          = 15

  environment {

    variables = {

      DJANGO_WEBHOOK_URL = "http://${aws_instance.squadhost_server.public_ip}:8000/api/servers/webhook/status"
      WEBHOOK_SECRET     = random_password.webhook_secret.result

    }

  }

  tags = {

    Name       = "squadhost-status-updater"
    project    = "squadhost"
    managed_by = "terraform"

  }

}

# Lambda permissions, Allow S3 to invoke status_updater
resource "aws_lambda_permission" "allow_s3" {

  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.status_updater_lambda.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.squadhost_backups.arn

}
