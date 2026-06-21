# S3 bucket for storing world data
resource "random_id" "bucket_suffix" {

  byte_length = 8

}

resource "aws_s3_bucket" "squadhost_backups" {

  bucket        = "squadhost-backups-${random_id.bucket_suffix.hex}"
  force_destroy = true

  tags = {

    Name       = "squadhost_backups"
    project    = "squadhost"
    managed_by = "terraform"

  }

}


# DynamoDB creation
resource "aws_dynamodb_table" "servers" {

  name         = "squadhost-servers"
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "owner_id"
  range_key = "server_id"

  attribute {

    name = "owner_id"
    type = "S"

  }

  attribute {

    name = "server_id"
    type = "S"

  }

  global_secondary_index {

    name            = "server_id-index"
    hash_key        = "server_id"
    projection_type = "KEYS_ONLY"

  }

  tags = {

    Name       = "squadhost-servers"
    project    = "squdhost"
    managed_by = "terraform"

  }

}

# ---------------------------------------- TO BE REMOVED ------------------------------------
# Create RDS subnet group
resource "aws_db_subnet_group" "rds_subnet_group" {

  name       = "squadhost-db-subnet"
  subnet_ids = [aws_subnet.public_1.id, aws_subnet.public_2.id]

  tags = {

    Name       = "squadhost-db-subnet"
    project    = "squadhost"
    managed_by = "terraform"

  }

}

# Create Database instance
resource "aws_db_instance" "postgres" {

  identifier             = "squadhost-db"
  allocated_storage      = 20
  engine                 = "postgres"
  engine_version         = "16"
  instance_class         = "db.t3.micro"
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  skip_final_snapshot    = true
  publicly_accessible    = false

  tags = {

    Name       = "squadhost-db"
    project    = "squadhost"
    managed_by = "terraform"

  }

}
# ----------------------------------------------------------------------------------------------

# S3 bucket notification, (world save completion signal)
resource "aws_s3_bucket_notification" "bucket_notifications" {

  bucket = aws_s3_bucket.squadhost_backups.id

  lambda_function {

    lambda_function_arn = aws_lambda_function.status_updater_lambda.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".zip"

  }

  depends_on = [aws_lambda_permission.allow_s3]

}
