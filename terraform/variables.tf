variable "aws_region" {
  description = "AWS region where the DevConnect EC2 machine will be created."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for AWS resource names and tags."
  type        = string
  default     = "devconnect-pro"
}

variable "environment" {
  description = "Environment tag."
  type        = string
  default     = "lab"
}

variable "instance_type" {
  description = "EC2 instance type. t3.medium provides 2 vCPU and 4 GiB RAM, good for the base lab. Use t3.large/t3.xlarge for smoother monitoring demos."
  type        = string
  default     = "t3.medium"
}

variable "root_volume_size_gb" {
  description = "Root EBS volume size in GB."
  type        = number
  default     = 30
}

variable "root_volume_type" {
  description = "Root EBS volume type."
  type        = string
  default     = "gp3"
}

variable "allowed_ssh_cidr" {
  description = "CIDR allowed to SSH into EC2. For safer usage, set this to your public IP /32. Example: 203.0.113.10/32."
  type        = string
}

variable "allowed_http_cidr" {
  description = "CIDR allowed to access HTTP/HTTPS app ingress. Use 0.0.0.0/0 for public demo access."
  type        = string
  default     = "0.0.0.0/0"
}

variable "allowed_admin_cidr" {
  description = "CIDR allowed to access optional admin ports if enabled. Recommended: your public IP /32."
  type        = string
  default     = "127.0.0.1/32"
}

variable "existing_key_name" {
  description = "Existing AWS EC2 key pair name. If provided, Terraform will use this instead of creating a new key pair."
  type        = string
  default     = ""
}

variable "public_key_path" {
  description = "Path to local SSH public key used to create an AWS EC2 key pair when existing_key_name is empty."
  type        = string
  default     = "~/.ssh/devconnect_ec2.pub"
}

variable "associate_public_ip" {
  description = "Attach public IP to EC2. Keep true for a simple student lab in default VPC."
  type        = bool
  default     = true
}

variable "enable_k3s_api_access" {
  description = "Open Kubernetes API port 6443 to allowed_admin_cidr. Keep false unless you need remote kubectl directly from your laptop."
  type        = bool
  default     = false
}

variable "enable_monitoring_admin_ports" {
  description = "Open Grafana/ArgoCD/Prometheus/Loki admin ports to allowed_admin_cidr. Recommended false; use kubectl port-forward or SSH tunnel instead."
  type        = bool
  default     = false
}

variable "enable_ssm" {
  description = "Attach AWS Systems Manager role to the instance for optional Session Manager access."
  type        = bool
  default     = true
}

variable "extra_tags" {
  description = "Extra AWS tags to apply to resources."
  type        = map(string)
  default     = {}
}
