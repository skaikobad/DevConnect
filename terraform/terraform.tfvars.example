# AWS region
aws_region = "us-west-2"

# t3.medium = 2 vCPU / 4 GiB RAM. Good minimum for lab.
# For smoother Grafana/Prometheus/ArgoCD demos, use t3.large.
instance_type = "t3.large"

# 30 GB encrypted gp3 EBS root volume
root_volume_size_gb = 30
root_volume_type    = "gp3"

# IMPORTANT: Replace with your public IP /32.
# Find your IP: curl https://checkip.amazonaws.com
allowed_ssh_cidr = "0.0.0.0/0"

# App HTTP/HTTPS access. Keep 0.0.0.0/0 for public demo, or restrict to your IP.
allowed_http_cidr = "0.0.0.0/0"

# Admin CIDR for optional ports. Recommended: your public IP /32.
allowed_admin_cidr = "0.0.0.0/0"

# If you already have an AWS key pair, set its name here and Terraform will not create a new one.
existing_key_name = "my-existing-keypair"

# If existing_key_name is empty, Terraform creates an AWS key pair using this public key.
public_key_path = "~/.ssh/devconnect_ec2.pub"

# Keep these false. Use kubectl port-forward or SSH tunnel for Grafana/ArgoCD/Prometheus.
enable_k3s_api_access          = false
enable_monitoring_admin_ports = false

enable_ssm = true

extra_tags = {
  Course = "bongoDev Batch 5"
}
