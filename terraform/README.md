# Terraform EC2 Provisioning for DevConnect Pro

This Terraform module creates one EC2 machine for the DevConnect Pro end-to-end DevOps lab.

It provisions:

- Ubuntu 22.04 EC2 instance
- Default instance size: `t3.medium` for 4 GiB RAM
- 30 GB encrypted `gp3` EBS root volume
- Security group with essential app ports
- SSH access restricted by CIDR
- Optional SSM Session Manager role
- Basic OS packages and Kubernetes-friendly sysctl settings

## What this Terraform does not do

Terraform creates the EC2 machine and network access. It does **not** automatically deploy the full app by itself.

After EC2 is ready, use the project bootstrap scripts:

```bash
./scripts/01-install-docker.sh
./scripts/02-install-k3s.sh
./scripts/03-install-argocd.sh
./scripts/04-install-monitoring.sh
REPO_URL=https://github.com/<org>/<repo>.git ./scripts/05-bootstrap-devconnect.sh
```

## Prerequisites on your local machine

Install:

- Terraform
- AWS CLI
- SSH client

Configure AWS credentials:

```bash
aws configure
```

or export environment variables:

```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_DEFAULT_REGION="us-east-1"
```

## Step 1: Create an SSH key

```bash
ssh-keygen -t ed25519 -f ~/.ssh/devconnect_ec2 -N "" -C "devconnect-pro"
```

This creates:

```text
~/.ssh/devconnect_ec2
~/.ssh/devconnect_ec2.pub
```

Terraform will upload the public key to AWS as an EC2 key pair.

## Step 2: Configure Terraform variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Find your public IP:

```bash
curl https://checkip.amazonaws.com
```

Edit `terraform.tfvars`:

```hcl
allowed_ssh_cidr  = "YOUR_PUBLIC_IP/32"
allowed_admin_cidr = "YOUR_PUBLIC_IP/32"
```

Recommended starting values:

```hcl
instance_type       = "t3.medium"
root_volume_size_gb = 30
allowed_http_cidr   = "0.0.0.0/0"
```

For smoother monitoring demos, use:

```hcl
instance_type = "t3.large"
root_volume_size_gb = 50
```

## Step 3: Create the EC2 instance

```bash
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
```

Type `yes` when Terraform asks for approval.

## Step 4: SSH into EC2

Terraform prints an `ssh_command` output. Example:

```bash
ssh -i ~/.ssh/devconnect_ec2 ubuntu@<EC2_PUBLIC_IP>
```

## Step 5: Install DevConnect platform stack on EC2

On the EC2 machine:

```bash
sudo apt update
sudo apt install -y git unzip curl

git clone https://github.com/<org>/<repo>.git
cd <repo>
chmod +x scripts/*.sh

./scripts/01-install-docker.sh
./scripts/02-install-k3s.sh
./scripts/03-install-argocd.sh
./scripts/04-install-monitoring.sh
REPO_URL=https://github.com/<org>/<repo>.git ./scripts/05-bootstrap-devconnect.sh
```

## Step 6: Use Terraform output in GitHub Secrets

Get EC2 IP:

```bash
terraform output -raw public_ip
```

Add this to GitHub Actions secrets:

```text
EC2_HOST=<terraform public_ip output>
EC2_USER=ubuntu
EC2_SSH_PORT=22
EC2_SSH_PRIVATE_KEY=<contents of ~/.ssh/devconnect_ec2>
```

Get private key content:

```bash
cat ~/.ssh/devconnect_ec2
```

## Ports opened by default

| Port | Purpose | Source |
|---:|---|---|
| 22 | SSH | `allowed_ssh_cidr` |
| 80 | HTTP app ingress | `allowed_http_cidr` |
| 443 | HTTPS app ingress | `allowed_http_cidr` |

Optional ports are disabled by default:

| Port | Purpose |
|---:|---|
| 6443 | Kubernetes API |
| 3001 | Grafana if manually exposed |
| 8080 | ArgoCD if manually exposed |
| 9090 | Prometheus if manually exposed |
| 9093 | Alertmanager if manually exposed |
| 3100 | Loki if manually exposed |

Keep optional ports closed and use `kubectl port-forward` or SSH tunnels for safer lab access.

## Destroy resources

When finished:

```bash
terraform destroy
```

This deletes the EC2 machine, security group, and attached root EBS volume.


Hello