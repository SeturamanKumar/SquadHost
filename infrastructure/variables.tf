variable "aws_region" {
  description = "The AWS region to deploy Squadhost into"
  type        = string
  default     = "ap-south-1"
}

# --------------------------------------------- TO BE REMOVED ---------------------------------------------------
variable "db_username" {
  description = "The administrator username for the RDS postgresSQL database"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "The administrator password for the RDS postgresSQL database"
  type        = string
  sensitive   = true
}
# -----------------------------------------------------------------------------------------------------------------

