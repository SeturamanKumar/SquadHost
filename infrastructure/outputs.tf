output "squadhost_server_ip" {
    description = "The public IP address of the Next.js/Django EC2 server"
    value = aws_instance.squadhost_server.public_ip
}

output "s3_backup_bucket_name" {
    description = "The globally unique name of the S3 backup bucket"
    value = aws_s3_bucket.squadhost_backups.bucket
}

output "rds_endpoint" {
    description = "The connection URL for the PostgreSQL database"
    value = aws_db_instance.postgres.endpoint
}

output "db_username" {
    description = "The administrator username for the RDS postgresSQL database"
    value = var.db_username
    sensitive = true
}

output "db_password" {
    description = "The administrator password for the RDS postgresSQL database"
    value = var.db_password
    sensitive = true
}

output "webhook_secret" {
    description = "The securely generated webhook password for Django and Lambda"
    value = random_password.webhook_secret.result
    sensitive = true
}