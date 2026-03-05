data "aws_ami" "ubuntu" {
    most_recent = true
    owners = ["099720109477"]

    filter {
        name = "name"
        values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
    }

    filter {
        name = "virtualization-type"
        values = ["hvm"]
    }
}

data "archive_file" "create_server_zip" {
    type = "zip"
    source_dir = "${path.module}/lambdas/create_server"
    output_path = "${path.module}/lambdas/create_server.zip"
}

resource "aws_iam_role" "lambda_ec2_role" {
    name = "squadhost_lambda_ec2_role"
    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [{
            Action = "sts:AssumeRole"
            Effect = "Allow"
            Principal = {
                Service = "lambda.amazonaws.com"
            }
        }]
    })
}

resource "aws_iam_role_policy" "lambda_ec2_policy" {
    name = "squadhost_lambda_ec2_policy"
    role = aws_iam_role.lambda_ec2_role.id
    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect = "Allow"
                Action = ["ec2:RunInstances", "ec2:CreateTags"]
                Resource = "*"
            },
            {
                Effect = "Allow"
                Action = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
                Resource = "arn:aws:logs:*:*:*"
            }
        ]
    })
}

resource "aws_lambda_function" "create_server_lambda" {
    filename = data.archive_file.create_server_zip.output_path
    function_name = "squadhost_create_server"
    role = aws_iam_role.lambda_ec2_role.arn
    handler = "lambda_function.lambda_handler"
    runtime = "python3.12"
    source_code_hash = data.archive_file.create_server_zip.output_base64sha256

    environment {
        variables = {
            S3_BACKUP_BUCKET = aws_s3_bucket.squadhost_backup.bucket
            WORKER_AMI_ID = data.aws_ami.ubuntu.id
        }
    }
}

resource "aws_iam_role" "ec2_worker_role" {
    name = "squadhost_ec2_worker_role"
    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [{
            Action = "sts:AssumeRole"
            Effect = "Allow"
            Principal = {
                Service = "ec2.amazonaws.com"
            }
        }]
    })
}

resource "aws_iam_role_policy" "ec2_worker_s3_policy" {
    name = "squadhost_ec2_worker_s3_policy"
    role = aws_iam_role.ec2_worker_role.id
    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [{
            Effect = "Allow"
            Action = ["s3:PutObject", "s3:GetObject", "s3:ListBucket"]
            Resource = [aws_s3_bucket.squadhost_backup.arn, "${aws_s3_bucket.squadhost_backup.arn}/*"]
        }]
    })
}

resource "aws_iam_instance_profile" "ec2_worker_profile" {
    name = "squadhost_worker_profile"
    role = aws_iam_role.ec2_worker_role.name
}

data "archive_file" "lambda_s3_role" {
    name = "squadhost_lambda_s3_role"
    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [{
            Action = "sts:AssumeRole"
            Effect = "Allow"
            Principal = {
                Service = "lambda.amazonaws.com"
            }
        }]
    })
}

resource "aws_iam_role" "lambda_s3_role" {
    name = "squadhost_lambda_s3_role"
    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [{
            Action = "sts:AssumeRole"
            Effect = "Allow"
            Principal = {
                Service = "lambda.amazonaws.com"
            }
        }]
    })
}

resource "aws_iam_role_policy" "lambda_s3_policy" {
    name = "squadhost_lambda_s3_policy"
    role = aws_iam_role.lambda_s3_role.id
    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [{
            Effect = "Allow"
            Action = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
            Resource = "arn:aws:logs:*:*:*"
        }]
    })
}

resource "random_password" "webhook_secret" {
    length = 32
    special = false
}

resource "aws_lambda_function" "status_updater_lambda" {
    filename = data.archive_file.status_updater_zip.output_path
    function_name = "squadhost_status_updater"
    role = aws_iam_role.lambda_s3_role.arn
    handler = "lambda_function.lambda_handler"
    runtime = "python3.12"
    source_code_hash = data.archive_file.status_updater_zip.output_base64sha256

    environment {
        variables = {
            DJANGO_WEBHOOK_URL = "http://${aws_instance.squadhost_server.public_ip}:8000/webhook/status"
            WEBHOOK_SECRET = random_password.webhook_secret.result
        }
    }
}

resource "aws_lambda_permission" "allow_s3" {
    statement_id = "AllowExecutionFromS3Bucket"
    action = "lambda:InvokeFunction"
    function_name = aws_lambda_function.status_updater_lambda.function_name
    principal = "s3.amazonaws.com"
    source_arn = aws_s3_bucket.squadhost_backup.arn
}

resource "aws_s3_bucket_notification" "bucket_notification" {
    bucket = aws_s3_bucket.squadhost_backup.id

    lambda_function {
        lambda_function_arn = aws_lambda_function.status_updater_lambda.arn
        events = ["s3:ObjectCreated:*]
        filter_suffix = ".zip"
    }

    depends_on = [aws_lambda_permission.allow_s3]
}