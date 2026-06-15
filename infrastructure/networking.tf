# Created VPC for SquadHost
resource "aws_vpc" "main" {

  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true

  tags = {

    Name       = "squadhost-vpc"
    project    = "squadhost"
    managed_by = "terraform"

  }

}

# Create an internet_gateway for main VPC
resource "aws_internet_gateway" "igw" {

  vpc_id = aws_vpc.main.id

  tags = {

    Name       = "squadhost-igw"
    project    = "squadhost"
    managed_by = "terraform"

  }

}

# Creating subnet 1 for main VPC
resource "aws_subnet" "public_1" {

  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {

    Name       = "squadhost-public-1"
    project    = "squadhost"
    managed_by = "terraform"

  }

}

# Creating subnet 2 for main VPC
resource "aws_subnet" "public_2" {

  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "${var.aws_region}b"
  map_public_ip_on_launch = true

  tags = {

    Name       = "squadhost-public-2"
    project    = "squadhost"
    managed_by = "terraform"

  }

}

# Make route table for public internet gateway
resource "aws_route_table" "public_rt" {

  vpc_id = aws_vpc.main.id

  route {

    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id

  }

  tags = {

    Name       = "squadhost-public-rt"
    project    = "squadhost"
    managed_by = "terraform"

  }

}

# Add subnet 1 in route table
resource "aws_route_table_association" "public_1_assoc" {

  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.public_rt.id

}

# Add subnet 2 in route table
resource "aws_route_table_association" "public_2assoc" {

  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public_rt.id

}

# Attach security group to VPC
resource "aws_security_group" "ec2_sg" {

  name   = "squadhost-ec2-sg"
  vpc_id = aws_vpc.main.id

  ingress {

    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]

  }

  ingress {

    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]

  }

  ingress {

    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]

  }

  ingress {

    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]

  }

  ingress {

    from_port   = 25565
    to_port     = 25565
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]

  }

  egress {

    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]

  }

  tags = {

    Name       = "squadhost-ec2-sg"
    project    = "squadhost"
    managed_by = "terraform"

  }

}

# RDS security group
resource "aws_security_group" "rds_sg" {

  name   = "squadhost-rds-sg"
  vpc_id = aws_vpc.main.id

  ingress {

    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2_sg.id]

  }

  egress {

    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]

  }

  tags = {

    Name       = "squadhost-rds-sg"
    project    = "squadhost"
    managed_by = "terraform"

  }

}
