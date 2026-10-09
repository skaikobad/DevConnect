output "instance_id" {
  description = "EC2 instance ID."
  value       = aws_instance.devconnect.id
}

output "public_ip" {
  description = "EC2 public IP address."
  value       = aws_instance.devconnect.public_ip
}

output "public_dns" {
  description = "EC2 public DNS name."
  value       = aws_instance.devconnect.public_dns
}

output "ssh_command" {
  description = "SSH command to connect to the EC2 instance."
  value       = "ssh -i ${replace(pathexpand(var.public_key_path), ".pub", "")} ubuntu@${aws_instance.devconnect.public_ip}"
}

output "github_secret_ec2_host" {
  description = "Use this value for GitHub secret EC2_HOST."
  value       = aws_instance.devconnect.public_ip
}

output "next_steps" {
  description = "Next command sequence after EC2 is created."
  value       = <<EOT
1. SSH into the instance using the ssh_command output.
2. Clone your DevConnect repository.
3. Run:
   chmod +x scripts/*.sh
   ./scripts/01-install-docker.sh
   ./scripts/02-install-k3s.sh
   ./scripts/03-install-argocd.sh
   ./scripts/04-install-monitoring.sh
   REPO_URL=https://github.com/<org>/<repo>.git ./scripts/05-bootstrap-devconnect.sh
EOT
}
