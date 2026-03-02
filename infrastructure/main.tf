terraform {
    required_providers {
        aws = {
            source = "hashicorp/aws"
            version = "~> 5.0"
        }
    }
    backend "s3" {}
}

provider "aws" {
    region = var.aws_region
}

resource "random_id" "bucket_suffix" {
    byte_length = 8
}

resource "aws_s3_bucket" "squadhost_backups" {
    bucket = "squadhost-backups-${random_id.bucket_suffix.hex}"
    force_destroy = true
}

resource "aws_vpc" "main" {
    cidr_block = "10.0.0.0/16"
    enable_dns_hostnames = true
}

resource "aws_internet_gateway" "igw" {
    vpc_id = aws_vpc.main.id
}

resource "aws_subnet" "public_1" {
    vpc_id = aws_vpc.main.id
    cidr_block = "10.0.1.0/24"
    availability_zone = "ap-south-1a"
    map_public_ip_on_launch = true
}

resource "aws_subnet" "public_2" {
    vpc_id = aws_vpc.main.id
    cidr_block = "10.0.2.0/24"
    availability_zone = "ap-south-1b"
    map_public_ip_on_launch = true
}

resource "aws_route_table" "public_rt" {
    vpc_id = aws_vpc.main.id
    route {
        cidr_block = "0.0.0.0/0"
        gateway_id = aws_internet_gateway.igw.id
    }
}

resource "aws_route_table_association" "public_1_assoc" {
    subnet_id = aws_subnet.public_1.id
    route_table_id = aws_route_table.public_rt.id
}

resource "aws_route_table_association" "public_2_assoc" {
    subnet_id = aws.subnet_id.public_2.id
    route_table_id = aws_route_table.public_rt.id
}

resource "aws_security_group" "ec2_sg" {
    name = "squadhost-ec2-sg"
    vpc_id = aws_vpc.main.id

    ingress {
        from_port = 22
        to_port = 22
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    ingress {
        from_port = 80
        to_port = 80
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    ingress {
        from_port = 25565
        to_port = 25600
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }
}

resource "aws_security_group" "rds_sg" {
    name = "squadhost-rds-sg"
    vpc_id = aws_vpc.main.id

    ingress {
        from_port = 5432
        to_port = 5432
        protocol = "tcp"
        security_groups = [aws_security_group.ec2_sg.id]
    }

    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }
}

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
}

resource "aws_iam_role_policy" "kamikaze_policy" {
    name = "squadhost_kamikaze_policy"
    role = aws_iam_role.ec2_kamikaze_role.id

    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = ["s3:PutObject", "s3:GetObject", "s3:ListBucket"]
                Effect = "Allow"
                Resource = [aws_s3_bucket.squadhost_backups.arn, "${aws_s3_bucket.squadhost_backups.arn}/*"]
            },
            {
                Action = ["ec2:TerminateInstances", "rds:DeleteDBInstance"]
                Effect = "Allow"
                Resource = "*"
            }
        ]
    })
}

resource "aws_iam_instance_profile" "ec2_profile" {
    name = "squadhost_ec2_profile"
    role = aws_iam_role.ec2_kamikaze_role.name
}

resource "aws_db_subnet_group" "rds_subnet_group" {
    name = "squadhost-db-subnet"
    subnet_ids = [aws_subnet.public_1.id, aws_subnet.public_2.id]
}

resource "aws_db_instance" "postgres" {
    identifier = "squadhost-db"
    allocated_storage = 20
    engine = "postgres"
    engine_version = "16.3"
    instance_class = "db.t3.micro"
    username = var.db_username
    password = var.db_password
    db_subnet_group_name = aws_db_subnet_group.rds_subnet_group.name
    vpc_security_group_ids = [aws_security_group.rds_sg.id]
    skip_final_snapshot = true
    publicly_accessible = false
}

data "aws_ami" "ubuntu" {
    most_recent = true
    owners = ["099720109477"]

    filter {
        name = "name"
        values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
    }

    filter {
        name = "virtualization-type"
        values = ["hvm"]
    }
}

resource "aws_instance" "squadhost_server" {
    ami = "ami-03f4878755434977f"
    instance_type = "t3.small"
    subnet_id = aws_subnet.public_1.id
    vpc_security_group_ids = [aws_security_group.ec2_sg.id]
    iam_instance_profile = aws_iam_instance_profile.ec2_profile.name

    associate_public_ip_address = true

    tags = {
        Name = "Squadhost-Kamikaze-Node"
    }
}