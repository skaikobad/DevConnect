provider "aws" {
  region = var.aws_region
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

locals {
  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = "bongoDev"
    },
    var.extra_tags
  )

  key_name = var.existing_key_name != "" ? var.existing_key_name : aws_key_pair.devconnect[0].key_name
}

resource "aws_key_pair" "devconnect" {
  count      = var.existing_key_name == "" ? 1 : 0
  key_name   = "${var.project_name}-${var.environment}-key"
  public_key = file(pathexpand(var.public_key_path))

  tags = local.common_tags
}

resource "aws_security_group" "devconnect" {
  name        = "${var.project_name}-${var.environment}-sg"
  description = "Security group for DevConnect Pro k3s EC2 lab"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH from allowed CIDR"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  ingress {
    description = "HTTP app ingress"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.allowed_http_cidr]
  }

  ingress {
    description = "HTTPS app ingress"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.allowed_http_cidr]
  }

  dynamic "ingress" {
    for_each = var.enable_k3s_api_access ? [1] : []
    content {
      description = "Kubernetes API server - admin CIDR only"
      from_port   = 6443
      to_port     = 6443
      protocol    = "tcp"
      cidr_blocks = [var.allowed_admin_cidr]
    }
  }

  dynamic "ingress" {
    for_each = var.enable_monitoring_admin_ports ? toset([3001, 8080, 9090, 9093, 3100]) : []
    content {
      description = "Optional admin/monitoring port ${ingress.value} - admin CIDR only"
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = [var.allowed_admin_cidr]
    }
  }

  egress {
    description = "Allow all outbound traffic for package installs, Docker pulls, GitHub, DockerHub, and Helm charts"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-sg" })
}

resource "aws_iam_role" "ssm" {
  count = var.enable_ssm ? 1 : 0
  name  = "${var.project_name}-${var.environment}-ssm-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  count      = var.enable_ssm ? 1 : 0
  role       = aws_iam_role.ssm[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ssm" {
  count = var.enable_ssm ? 1 : 0
  name  = "${var.project_name}-${var.environment}-ssm-profile"
  role  = aws_iam_role.ssm[0].name

  tags = local.common_tags
}

resource "aws_instance" "devconnect" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = data.aws_subnets.default.ids[0]
  vpc_security_group_ids      = [aws_security_group.devconnect.id]
  associate_public_ip_address = var.associate_public_ip
  key_name                    = local.key_name
  iam_instance_profile        = var.enable_ssm ? aws_iam_instance_profile.ssm[0].name : null

  root_block_device {
    volume_size           = var.root_volume_size_gb
    volume_type           = var.root_volume_type
    encrypted             = true
    delete_on_termination = true
  }

  user_data = file("${path.module}/user-data.sh")

  metadata_options {
    http_tokens = "required"
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-ec2" })
}
