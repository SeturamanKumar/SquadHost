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

# create zip of lambda function (create_server)
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
  layers           = [aws_lambda_layer_version.worker_provisioning.arn]

  environment {

    variables = {

      SERVERS_TABLE      = aws_dynamodb_table.servers.name
      S3_BACKUP_BUCKET   = aws_s3_bucket.squadhost_backups.bucket
      WORKER_AMI_ID      = data.aws_ami.ubuntu.id
      SECURITY_GROUP_ID  = aws_security_group.ec2_sg.id
      SUBNET_ID          = aws_subnet.public_1.id
      INSTANCE_PROFILE   = aws_iam_instance_profile.ec2_worker_profile.name
      AWS_DEPLOY_REGION  = var.aws_region
      INSTANCE_PROFILE   = aws_iam_instance_profile.ec2_worker_profile.name
      DJANGO_WEBHOOK_URL = "REPLACE_WITH_API_GATEWAY_STATUS_WEBHOOK_URL" # TODO: API gateway doesn't exist yet
      WEBHOOK_SECRET     = "REPLACE_WITH_SECRETS_MANAGER_SECRET_NAME"    # TODO: secrets.tf has no playit.gg secret yet

    }

  }

  tags = {

    Name       = "squadhost-create-server"
    project    = "squadhost"
    managed_by = "terraform"

  }

}

# create zip of lambda function (status_updater)
data "archive_file" "status_updater_zip" {

  type        = "zip"
  source_dir  = "${path.module}/lambdas/status_updater"
  output_path = "${path.module}/lambdas/status_updater.zip"

}

# status updater lambda function
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

# Create zip of shared lambda layer
data "archive_file" "worker_provisioning_layer_zip" {

  type        = "zip"
  source_dir  = "${path.module}/lambdas/layers/worker_provisioning"
  output_path = "${path.module}/lambdas/layers/worker_provisioning.zip"

}

# store the zipped layer as common code for create and restart server
resource "aws_lambda_layer_version" "worker_provisioning" {

  filename            = data.archive_file.worker_provisioning_layer_zip.output_path
  layer_name          = "squadhost-worker-provisioning"
  source_code_hash    = data.archive_file.worker_provisioning_layer_zip.output_base64sha256
  compatible_runtimes = ["python3.12"]

}

# Create zip of lambda_function (list_servers)
data "archive_file" "list_servers_zip" {

  type        = "zip"
  source_dir  = "${path.module}/lambdas/list_servers"
  output_path = "${path.module}/lambdas/list_servers.zip"

}

# List server lambda function
resource "aws_lambda_function" "list_servers_lambda" {

  filename         = data.archive_file.list_servers_zip.output_path
  function_name    = "squadhost_list_servers"
  role             = aws_iam_role.lambda_read_role.arn
  handler          = "lambda_function.handler_handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.list_servers_zip.output_base64sha256
  timeout          = 10


  environment {

    variables = {
      SERVERS_TABLE = aws_dynamodb_table.servers.name
    }

  }

  tags = {

    Name       = "squadhost-list-servers"
    project    = "squadhost"
    managed_by = "terraform"

  }

}

# Create zip of lamdba_function (get_server)
data "archive_file" "get_server_zip" {

  type        = "zip"
  source_dir  = "${path.module}/lambdas/get_server"
  output_path = "${path.module}/lambdas/get_server.zip"

}

# Get server lambda function
resource "aws_lambda_function" "get_server_lambda" {

  filename         = data.archive_file.get_server_zip.output_path
  function_name    = "squadhost_get_server"
  role             = aws_iam_role.lambda_read_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.get_server_zip.output_base64sha256
  timeout          = 10

  environment {

    variables = {
      SERVERS_TABLE = aws_dynamodb_table.servers.name
    }

  }

  tags = {

    Name       = "squadhost-get-server"
    project    = "squadhost"
    managed_by = "terraform"

  }

}

# Create zip of lambda_function (delete_server)
data "archive_file" "delete_server_zip" {

  type        = "zip"
  source_dir  = "${path.module}/lambdas/delete_server"
  output_path = "${path.module}/lambdas/delete_server.zip"

}

# Delete server lambda function
resource "aws_lambda_function" "delete_server" {

  filename         = data.archive_file.delete_server_zip.output_path
  function_name    = "squadhost_delete_server"
  role             = aws_iam_role.lambda_ec2_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.delete_server_zip.output_base64sha256
  timeout          = 30

  environment {

    variables = {
      SERVERS_TABLE    = aws_dynamodb_table.servers.name
      S3_BACKUP_BUCKET = aws_s3_bucket.squadhost_backups.bucket
    }

  }

  tags = {

    Name       = "squadhost-delete-server"
    project    = "squadhost"
    managed_by = "terraform"

  }

}
