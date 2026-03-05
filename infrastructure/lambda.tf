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
                Action = ["ec2:RunInstance", "ec2:CreateTags"]
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

    enviornment = {
        variables = {
            S3_BACKUP_BUCKET = aws_s3_bucket.squadhost_backup.bucket
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