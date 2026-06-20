terraform {

  required_version = ">= 1.15.6"

  required_providers {

    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }

    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }

    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }

    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }

    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }

  }

  backend "s3" {
    key = "squadhost/terraform.tfstate"
  }

}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

