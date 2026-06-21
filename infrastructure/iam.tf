# IAM role for the master node with Kamikaze script
resource "aws_iam_role" "ec2_kamikaze_role" {

  name = "squadhost_kamikaze_role"

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

  tags = {

    Name       = "squadhost-kamikaze-role"
    project    = "squadhost"
    managed_by = "terraform"

  }

}

# IAM role policy for the master node with Kamikaze script
resource "aws_iam_role_policy" "kamikaze_policy" {

  name = "squadhost_kamikaze_policy"
  role = aws_iam_role.ec2_kamikaze_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # World backup and state bucket access
        Action = ["s3:PutObject", "s3:GetObject", "s3:ListBucket"]
        Effect = "Allow"
        Resource = [
          aws_s3_bucket.squadhost_backups.arn,
          "${aws_s3_bucket.squadhost_backups.arn}/*",
          "arn:aws:s3:::squadhost-tfstate-${data.aws_caller_identity.current.account_id}",
          "arn:aws:s3:::squadhost-tfstate-${data.aws_caller_identity.current.account_id}/*",
        ]
      },
      {
        # Self-Termination and RDS takedown for kamikaze script
        Action   = ["ec2:TerminateInstances", "ec2:DescribeInstances"]
        Effect   = "Allow"
        Resource = "*"
      },
      {
        # ------------------------------ TO BE REMOVED -------------------------
        Action   = ["rds:DeleteDBInstance"]
        Effect   = "Allow"
        Resource = "*"
        # ----------------------------------------------------------------------
      },
      {
        # Invoke Lambda funcitons during shutting down sequence
        Action   = ["lambda:InvokeFunction"]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })

}

# EC2 instance taking the role and policy
resource "aws_iam_instance_profile" "ec2_profile" {

  name = "squadhost_ec2_profile"
  role = aws_iam_role.ec2_kamikaze_role.name

  tags = {

    Name       = "squadhost-ec2-profile"
    project    = "squadhost"
    managed_by = "terraform"

  }

}

# IAM role for create server lambda
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

  tags = {

    Name       = "squadhost-lambda-ec2-role"
    project    = "squadhost"
    managed_by = "terraform"

  }

}

# IAM policies for create server lambda
resource "aws_iam_role_policy" "lambda_ec2_policy" {

  name = "squadhost_lambda_ec2_policy"
  role = aws_iam_role.lambda_ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Provision and manage EC2 instances
        Effect   = "Allow"
        Action   = ["ec2:RunInstances", "ec2:CreateTags", "ec2:DescribeInstances", "ec2:TerminateInstances"]
        Resource = "*"
      },
      {
        # Required to attach worker IAM role to new EC2 instances
        Effect   = "Allow"
        Action   = ["iam:PassRole"]
        Resource = "*"
      },
      {
        # Cloudwatch Logging
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        # DynamoDB create/delete/restart
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:UpdateItem", "dynamodb:DeleteItem", "dynamodb:Query"]
        Resource = aws_dynamodb_table.servers.arn
      }
    ]
  })

}

# Worker EC2 roles, for the game servers
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

  tags = {

    Name       = "squadhost-ec2-worker-role"
    project    = "squadhost"
    managed_by = "terraform"

  }

}

# Worker EC2 policies, for the game servers
resource "aws_iam_role_policy" "ec2_worker_s3_policy" {

  name = "squadhost_ec2_worker_s3_policy"
  role = aws_iam_role.ec2_worker_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      # World save permission and self-termination
      Effect   = "Allow"
      Action   = ["s3:PutObject", "s3:GetObject", "s3:ListBucket", "ec2:TerminateInstances"]
      Resource = "*"
    }]
  })

}

# EC2 worker taking the roles and policies
resource "aws_iam_instance_profile" "ec2_worker_profile" {

  name = "squadhost_worker_profile"
  role = aws_iam_role.ec2_worker_role.name

  tags = {

    Name       = "squadhost-worker-profile"
    project    = "squadhost"
    managed_by = "terraform"

  }

}

# IAM role for status updater lambda
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

  tags = {

    Name       = "squadhost-lambda-s3-role"
    project    = "squadhost"
    managed_by = "terraform"

  }

}

# IAM policies for status updater lambda
resource "aws_iam_role_policy" "lambda_s3_policy" {

  name = "squadhost_lamdba_s3_policy"
  role = aws_iam_role.lambda_s3_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Cloudwatch logging only
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        # Update DynamoDB of world saving
        Effect  = "Allow"
        Action  = ["dynamodb:UpdateItem"]
        Resouce = aws_dynamodb_table.servers.arn
      }
    ]
  })

}
