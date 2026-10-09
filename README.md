# DevConnect Pro — End-to-End DevOps Deployment Guide

DevConnect Pro is a 10-service microservices-style social application for DevOps and Cloud Engineering students. The project starts locally with Docker Compose and then moves into a complete CI/CD + Kubernetes + GitOps + Monitoring deployment on an EC2 machine.

DockerHub username configured in this project: **`bongodev`**

---

## 1. What you will deploy

### Application services

| # | Service | Purpose | Local Port | Kubernetes Workload |
|---|---|---|---|---|
| 1 | `frontend` | React UI served by Nginx | `3000` | Deployment + Service |
| 2 | `auth-service` | Register, login, JWT authentication | `8001` | Deployment + Service |
| 3 | `user-service` | User profile and user data | `8002` | Deployment + Service |
| 4 | `post-service` | Accepts post creation requests, pushes jobs to Redis Queue, supports public image URLs | `8003` | Deployment + Service |
| 5 | `like-service` | Post likes | `8004` | Deployment + Service |
| 6 | `comment-service` | Comments, optional comment image URL, comment likes | `8005` | Deployment + Service |
| 7 | `analytics-service` | Metrics, impressions, queue status, Redis counters | `8006` | Deployment + Service |
| 8 | `worker-service` | Consumes Redis Queue and creates posts in PostgreSQL | No public port | Deployment |
| 9 | `postgres` | Shared PostgreSQL database | `5432` | StatefulSet + Service + PVC |
| 10 | `redis` | Cache + queue backend | `6379` | StatefulSet + Service + PVC |



### Product experience update: Microservices Social Feed

The UI has been updated to make DevConnect feel like a more professional developer social application rather than only a technical demo. The authenticated home page is now named **Microservices Social Feed**.

Updated feed positioning:

```text
Connect with developers, share DevOps lessons, attach optional public images, and discuss ideas through comments and likes. Nginx routes the React experience to independent FastAPI services, while Redis Queue and the Worker Service process post creation asynchronously like a real cloud-native social platform.
```

The informational pages are also aligned with the latest project architecture:

- **Architecture** now explains the full path from GitHub Actions to DockerHub, ArgoCD, Kubernetes/k3s on EC2, DevConnect services, Redis Queue, PostgreSQL, and the Prometheus/Grafana/Loki observability stack.
- **Services** now describes both product services and DevOps platform services, including frontend, auth, user, post, worker, Redis, like, comment, analytics, PostgreSQL, CI/CD, GitOps, and monitoring.
- **Security** now explains professional controls across CI quality gates, container image scanning, GitOps deployment control, JWT authentication, secrets management, private data services, least-privilege networking, and observability.

This makes the app easier to present as a real-world social platform for developers to connect, share learning, and demonstrate end-to-end DevOps delivery.

### DevOps platform components

| Component | Purpose |
|---|---|
| GitHub Actions | CI/CD automation |
| DockerHub | Container image registry |
| Kubernetes/k3s | App runtime on EC2 |
| ArgoCD | GitOps deployment controller |
| Prometheus | Metrics collection, including DevConnect app-level `/prometheus` metrics and Worker `/metrics` |
| Grafana | Dashboards and visualization |
| Loki | Log storage |
| Grafana Alloy | Log collector that sends Kubernetes logs to Loki |
| node-exporter | EC2/node-level metrics |
| cAdvisor | Container-level resource metrics, adjusted for k3s/containerd paths |
| kube-state-metrics | Kubernetes object/status metrics |

---

## 2. End-to-end architecture

```text
Developer
  ↓
GitHub Pull Request / Push
  ↓
GitHub Actions
  ├── Tests
  ├── Frontend build
  ├── Trivy filesystem scan
  ├── OWASP Dependency-Check
  ├── SonarQube scan
  ├── Docker image build
  ├── Trivy image scan
  └── DockerHub push
        ↓
GitOps manifest update
        ↓
ArgoCD
        ↓
Kubernetes on EC2/k3s
        ↓
DevConnect App
  ├── Frontend
  ├── FastAPI microservices
  ├── PostgreSQL
  ├── Redis Queue
  └── Worker Service
        ↓
Observability
  ├── FastAPI app metrics at /prometheus
  ├── Worker metrics at /metrics on port 9100
  ├── Prometheus + ServiceMonitors
  ├── Grafana dashboards
  ├── Loki logs
  ├── Grafana Alloy
  ├── node-exporter
  ├── k3s/containerd-friendly cAdvisor
  └── kube-state-metrics
```

---

## 3. Recommended deployment flow

Follow this order carefully:

```text
1. Run the app locally with Docker Compose
2. Run tests locally
3. Push the project to GitHub
4. Add GitHub repository secrets
5. Push to main so GitHub Actions builds and pushes DockerHub images
6. Create an EC2 instance
7. Install Docker, k3s, ArgoCD, and monitoring on EC2
8. Bootstrap the ArgoCD application
9. ArgoCD syncs DevConnect to Kubernetes
10. Verify app, logs, metrics, and dashboards
```

Why this order matters:

- ArgoCD deploys Kubernetes manifests from Git.
- Kubernetes pulls Docker images from DockerHub.
- Therefore, images should exist in DockerHub before the first ArgoCD sync.

---

## 4. Prerequisites

### Local machine

Install:

```text
Git
Docker Desktop or Docker Engine
Docker Compose v2
Python 3.12+
Node.js 20+
A GitHub account
A DockerHub account
```

### Accounts and tokens

You need:

```text
GitHub repository
DockerHub access token
Optional SonarQube server/token
Optional SMTP credentials for email notification
```

For DockerHub, create an access token from DockerHub account settings and store it in GitHub Secrets as `DOCKERHUB_TOKEN`.

---

## 5. Local verification before GitHub

From the project root:

```bash
cp .env.example .env
docker compose up --build -d
```

Open:

```text
http://localhost:3000
```

Check containers:

```bash
docker compose ps
```

Expected services:

```text
frontend
auth-service
user-service
post-service
like-service
comment-service
analytics-service
worker-service
postgres
redis
```

Run API health checks:

```bash
curl http://localhost:3000/api/auth/health
curl http://localhost:3000/api/user/health
curl http://localhost:3000/api/post/health
curl http://localhost:3000/api/like/health
curl http://localhost:3000/api/comment/health
curl http://localhost:3000/api/analytics/health
```

Check Redis:

```bash
docker exec -it cloudconnect-redis redis-cli ping
```

Expected:

```text
PONG
```

Check worker logs:

```bash
docker compose logs -f worker-service
```

Create a post from the UI. The post request should go to Redis Queue, and the worker should consume it.

Check local app-level Prometheus metrics:

```bash
curl http://localhost:8001/prometheus | grep devconnect_http_requests_total
curl http://localhost:8003/prometheus | grep devconnect_post_create_requests_total
curl http://localhost:8006/prometheus | grep devconnect_impressions_tracked_total
curl http://localhost:9100/metrics | grep devconnect_worker_jobs_processed_total
```

Notes:

- FastAPI services expose Prometheus-compatible metrics at `/prometheus`.
- The Analytics product dashboard still uses `/api/analytics/metrics`, so Prometheus metrics use `/prometheus` to avoid route conflicts.
- The Worker Service exposes Prometheus metrics on port `9100` at `/metrics`.

---

## 6. Run tests locally

Install Python test dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
for file in services/*/requirements.txt; do python -m pip install -r "$file"; done
```

Run Python/project tests:

```bash
pytest
```

Run frontend tests and build:

```bash
cd frontend
npm install --legacy-peer-deps
npm test
npm run build
cd ..
```

The tests validate:

```text
Docker Compose service definition
Nginx API routes
Kubernetes manifest presence
Auth service routes
Post service queue behavior
Public image URL validation
Analytics routes and queue metrics
Worker queue usage
Frontend navigation and API helper behavior
```

---

## 7. Push project to GitHub

Create a new GitHub repository, then push the code:

```bash
git init
git add .
git commit -m "Initial DevConnect Pro end-to-end DevOps project"
git branch -M main
git remote add origin https://github.com/<your-org-or-user>/<your-repo>.git
git push -u origin main
```

If the repository already exists, use your existing remote.

---

## 8. GitHub repository secrets

Go to:

```text
GitHub Repository → Settings → Secrets and variables → Actions → New repository secret
```

Add these secrets:

| Secret | Required? | Purpose |
|---|---:|---|
| `DOCKERHUB_TOKEN` | Yes | Allows GitHub Actions to push images to DockerHub |
| `SONAR_TOKEN` | Optional | SonarQube analysis |
| `SONAR_HOST_URL` | Optional | SonarQube server URL |
| `EC2_HOST` | Required for CD verification | EC2 public IP or DNS used by GitHub Actions to SSH into k3s host |
| `EC2_USER` | Required for CD verification | EC2 SSH user, usually `ubuntu` |
| `EC2_SSH_PRIVATE_KEY` | Required for CD verification | Private key that can SSH into the EC2 machine |
| `EC2_SSH_PORT` | Optional | SSH port, default `22` |
| `SMTP_SERVER` | Required for email | Gmail SMTP server, use `smtp.gmail.com` |
| `SMTP_PORT` | Required for email | Gmail SMTP port, use `587` |
| `SMTP_USERNAME` | Required for email | Gmail address used to send bongoDev notifications |
| `SMTP_PASSWORD` | Required for email | Gmail App Password, not your normal Google password |
| `CI_EMAIL_RECIPIENT` | Required for email | Email recipient for CI/CD result |

### Gmail SMTP for bongoDev branded notifications

Use these values for Gmail-based CI/CD email notifications:

```text
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=<your-gmail-address>
SMTP_PASSWORD=<Google App Password>
CI_EMAIL_RECIPIENT=<recipient-email>
```

Important Gmail setup notes:

1. Enable 2-Step Verification on the Google account that will send email.
2. Create a Google App Password for GitHub Actions.
3. Store the App Password as `SMTP_PASSWORD` in GitHub Secrets.
4. Do not use your normal Gmail password.
5. The workflow sends a bongoDev branded HTML email for success or failure.

Important:

- Do not commit tokens, passwords, or SMTP credentials into Git.
- The demo Kubernetes secret is for lab use. Replace it with a safer secret management approach for real production.

---

## 9. GitHub Actions CI/CD behavior

Workflow file:

```text
.github/workflows/ci-cd.yml
```

### Pull request behavior

On pull request to `main`, the workflow runs:

```text
Python tests
Frontend tests
Frontend build
Trivy filesystem scan
OWASP Dependency-Check
SonarQube scan if secrets exist
Email notification if SMTP secrets exist
```

Pull requests do **not** push Docker images and do **not** deploy.

### Push to main behavior

On push to `main`, the workflow runs:

```text
Tests
Security scans
Build Docker images
Trivy image scans
Push images to DockerHub
Update k8s/overlays/prod/kustomization.yaml with the Git SHA tag
Commit/push GitOps manifest update
ArgoCD detects the change and deploys
GitHub Actions SSHes into EC2 and verifies ArgoCD is Synced + Healthy
GitHub Actions verifies Kubernetes rollout status and app metrics endpoints
Send bongoDev branded Gmail notification if configured
```

DockerHub images pushed by the pipeline:

```text
bongodev/devconnect-frontend
bongodev/devconnect-auth-service
bongodev/devconnect-user-service
bongodev/devconnect-post-service
bongodev/devconnect-like-service
bongodev/devconnect-comment-service
bongodev/devconnect-analytics-service
bongodev/devconnect-worker-service
```

Image tags:

```text
latest
<git-commit-sha>
```

The Git SHA tag is preferred for Kubernetes deployments because it gives traceability.

---

## 10. Important GitHub Actions care points

Before depending on the pipeline, check these:

1. **Actions permissions**

   Go to:

   ```text
   Repository → Settings → Actions → General → Workflow permissions
   ```

   Enable:

   ```text
   Read and write permissions
   ```

   This is required because the workflow commits updated image tags to `k8s/overlays/prod/kustomization.yaml`.

2. **Branch protection**

   If `main` is protected, the default `GITHUB_TOKEN` may not be able to push GitOps updates. Either:

   - allow GitHub Actions to push, or
   - use a separate Personal Access Token, or
   - use a separate GitOps repository.

3. **DockerHub rate/authentication**

   Make sure `DOCKERHUB_TOKEN` is valid. If image push fails, check the token and DockerHub username.

4. **Security gates**

   Trivy and OWASP can fail the build if critical/high vulnerabilities are found. For a student lab, this is useful. For live class demos, prepare for the possibility that public base images may suddenly receive new CVE reports.

5. **SonarQube optionality**

   SonarQube scan only runs if `SONAR_TOKEN` and `SONAR_HOST_URL` exist.

6. **ArgoCD runtime verification requires EC2 SSH secrets**

   The `cd-verify` job proves that the GitOps deployment really reached the EC2/k3s cluster. It SSHes into EC2 and checks:

   ```text
   ArgoCD application sync status = Synced
   ArgoCD application health status = Healthy
   Kubernetes rollout status for every app Deployment/StatefulSet
   FastAPI Prometheus endpoints
   Worker metrics endpoint
   ServiceMonitor resources
   ```

   Required secrets:

   ```text
   EC2_HOST
   EC2_USER
   EC2_SSH_PRIVATE_KEY
   EC2_SSH_PORT optional, defaults to 22
   ```

   Without these secrets, CI can build and push images, but CD runtime verification cannot prove the app is healthy in EC2.

7. **bongoDev branded email notifications**

   The `notify` job sends an HTML email showing:

   ```text
   Tests result
   Security result
   DockerHub result
   GitOps update result
   ArgoCD runtime verification result
   Workflow run link
   ```

   Gmail sender secrets are required for email delivery.

---

## 11. EC2 instance planning

Recommended EC2 instance for a smooth lab:

```text
OS: Ubuntu 22.04 or Ubuntu 24.04
Size: t3.large or larger recommended
Minimum: 2 vCPU, 8 GB RAM
Disk: 30 GB minimum, 50 GB better
```

Security Group inbound rules:

| Port | Purpose | Source |
|---|---|---|
| 22 | SSH | Your IP only |
| 80 | HTTP ingress | Your IP or public, depending on lab need |
| 443 | HTTPS / ArgoCD port-forward alternative | Your IP or public, depending on lab need |
| 3000 | Optional frontend port-forward demo | Your IP only |
| 3001 | Optional Grafana port-forward demo | Your IP only |
| 8080 | Optional ArgoCD port-forward demo | Your IP only |
| 9090 | Optional Prometheus port-forward demo | Your IP only |

Safer approach:

- Keep only port 22 open.
- Use SSH tunnel or `kubectl port-forward` for ArgoCD, Grafana, Prometheus, and app access.

---

## 12. Prepare the EC2 machine

SSH into EC2:

```bash
ssh -i <your-key.pem> ubuntu@<EC2_PUBLIC_IP>
```

Install basic tools:

```bash
sudo apt-get update -y
sudo apt-get install -y git curl unzip jq
```

Clone your GitHub repository:

```bash
git clone https://github.com/<your-org-or-user>/<your-repo>.git
cd <your-repo>
```

Make scripts executable:

```bash
chmod +x scripts/*.sh
```

---

## 13. Install Docker on EC2

Run:

```bash
./scripts/01-install-docker.sh
```

Then apply Docker group permission:

```bash
newgrp docker
```

Verify:

```bash
docker --version
docker compose version
```

---

## 14. Install k3s Kubernetes on EC2

Run:

```bash
./scripts/02-install-k3s.sh
```

Verify:

```bash
kubectl get nodes
kubectl get pods -A
```

Expected: one node in `Ready` state.

---

## 15. Install ArgoCD

Run:

```bash
./scripts/03-install-argocd.sh
```

Verify:

```bash
kubectl -n argocd get pods
```

All ArgoCD pods should eventually become `Running`.

Get the initial ArgoCD password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo
```

Access ArgoCD UI:

```bash
kubectl -n argocd port-forward svc/argocd-server 8080:443
```

Open:

```text
https://localhost:8080
```

Login:

```text
username: admin
password: <initial password from command above>
```

If working directly on a remote EC2 terminal, use SSH port forwarding from your local machine:

```bash
ssh -i <your-key.pem> -L 8080:localhost:8080 ubuntu@<EC2_PUBLIC_IP>
```

Then run the `kubectl port-forward` command on EC2.

---

## 16. Install monitoring stack

Run:

```bash
./scripts/04-install-monitoring.sh
```

This installs:

```text
Prometheus
Grafana
Alertmanager
Loki
Grafana Alloy
node-exporter
kube-state-metrics
cAdvisor
```

Verify:

```bash
kubectl -n monitoring get pods
kubectl -n monitoring get svc
```

Access Grafana:

```bash
kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3001:80
```

Open:

```text
http://localhost:3001
```

Demo login:

```text
admin / admin123
```

Access Prometheus:

```bash
kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090
```

Open:

```text
http://localhost:9090
```

The monitoring stack is configured to discover ServiceMonitor resources across namespaces. DevConnect adds ServiceMonitors for FastAPI services and the Worker Service after the app is deployed.

cAdvisor has been updated for k3s/containerd with host paths such as:

```text
/var/lib/containerd
/var/lib/kubelet
/run/containerd
```

This is safer for k3s than a Docker-only `/var/lib/docker` mount.

---

## 17. Bootstrap DevConnect through ArgoCD

Make sure your GitHub Actions pipeline has already pushed images to DockerHub at least once.

Then run:

```bash
REPO_URL=https://github.com/<your-org-or-user>/<your-repo>.git \
./scripts/05-bootstrap-devconnect.sh
```

If your branch is not `main`:

```bash
REPO_URL=https://github.com/<your-org-or-user>/<your-repo>.git \
BRANCH=<branch-name> \
./scripts/05-bootstrap-devconnect.sh
```

Verify ArgoCD application:

```bash
kubectl -n argocd get applications
kubectl -n argocd describe application devconnect
```

Verify app namespace:

```bash
kubectl -n devconnect get pods
kubectl -n devconnect get svc
kubectl -n devconnect get ingress
```

Wait until pods are running:

```bash
kubectl -n devconnect get pods -w
```

---

## 18. Access DevConnect app on Kubernetes

### Option A: Port-forward frontend service

```bash
kubectl -n devconnect port-forward svc/frontend 3000:80
```

Open:

```text
http://localhost:3000
```

If running on EC2, use SSH tunnel from your local machine:

```bash
ssh -i <your-key.pem> -L 3000:localhost:3000 ubuntu@<EC2_PUBLIC_IP>
```

Then run the `kubectl port-forward` command on EC2.

### Option B: Use Ingress host

The default Kubernetes overlay uses this host:

```text
devconnect.local
```

For local testing, map it to the EC2 public IP from your local machine:

```text
<EC2_PUBLIC_IP> devconnect.local
```

Add that line to your local `/etc/hosts`, then open:

```text
http://devconnect.local
```

This assumes your EC2 security group allows port 80 and k3s Traefik ingress is available.

---

## 19. Verify Kubernetes deployment

Check pods:

```bash
kubectl -n devconnect get pods -o wide
```

Check services:

```bash
kubectl -n devconnect get svc
```

Check frontend logs:

```bash
kubectl -n devconnect logs deploy/frontend --tail=100
```

Check API service logs:

```bash
kubectl -n devconnect logs deploy/auth-service --tail=100
kubectl -n devconnect logs deploy/post-service --tail=100
kubectl -n devconnect logs deploy/analytics-service --tail=100
```

Check worker logs:

```bash
kubectl -n devconnect logs deploy/worker-service -f
```

Check Redis queue from inside the cluster:

```bash
kubectl -n devconnect exec -it statefulset/redis -- redis-cli LLEN cloudconnect:queue:post-create
```

Check PostgreSQL tables:

```bash
kubectl -n devconnect exec -it statefulset/postgres -- \
  psql -U cloudconnect -d cloudconnect -c "\dt"
```

Check app-level Prometheus metrics inside Kubernetes:

```bash
kubectl -n devconnect exec deploy/auth-service -- \
  python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/prometheus').read().decode()[:500])"

kubectl -n devconnect exec deploy/post-service -- \
  python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/prometheus').read().decode()[:500])"

kubectl -n devconnect exec deploy/worker-service -- \
  python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:9100/metrics').read().decode()[:500])"
```

Check ServiceMonitors:

```bash
kubectl -n devconnect get servicemonitor
kubectl -n monitoring get servicemonitor cadvisor
```

In Prometheus UI, check:

```text
Status → Targets
```

Look for targets similar to:

```text
devconnect/auth-service/0
devconnect/post-service/0
devconnect/analytics-service/0
devconnect/worker-service/0
monitoring/cadvisor/0
```

Useful PromQL examples:

```promql
devconnect_http_requests_total
rate(devconnect_http_requests_total[5m])
devconnect_http_request_duration_seconds_bucket
devconnect_post_create_requests_total
devconnect_worker_jobs_processed_total
devconnect_worker_queue_depth
container_cpu_usage_seconds_total
container_memory_working_set_bytes
```

---

## 20. Test full app flow

1. Open the frontend.
2. Register a new user.
3. Login.
4. Create a post with text only.
5. Create a post with a public image URL.
6. Confirm the 2-second loader appears.
7. Watch the worker logs consume the post job.
8. Like the post.
9. Add a comment.
10. Add a comment with a public image URL.
11. Open Analytics.
12. Confirm users, posts, likes, comments, impressions, queue depth, and worker counters.

Worker validation:

```bash
kubectl -n devconnect logs deploy/worker-service -f
```

Analytics validation:

```bash
kubectl -n devconnect logs deploy/analytics-service --tail=100
```

---

## 21. CI/CD notification setup

GitHub Actions sends a bongoDev branded HTML email after pipeline completion when Gmail SMTP secrets are configured.

Use these GitHub Secrets:

```text
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=<your-gmail-address>
SMTP_PASSWORD=<Google App Password>
CI_EMAIL_RECIPIENT=<recipient-email>
```

The email includes:

```text
Pipeline status
Repository
Branch
Commit SHA
Actor
Tests result
Security result
Docker build/push result
GitOps update result
ArgoCD runtime verification result
Workflow run URL
```

For Gmail:

1. Turn on Google 2-Step Verification.
2. Create a Google App Password.
3. Store that App Password in GitHub Secrets as `SMTP_PASSWORD`.
4. Do not use your normal Gmail password.

If SMTP secrets are not configured, the pipeline still works but skips email notification.

---

## 22. Daily developer workflow

For a new feature:

```bash
git checkout -b feature/new-ui-change
# make changes
git add .
git commit -m "feat: update DevConnect UI"
git push -u origin feature/new-ui-change
```

Open a Pull Request to `main`.

PR pipeline runs:

```text
Tests
Frontend build
Trivy FS scan
OWASP Dependency-Check
SonarQube if configured
```

After merge to `main`:

```text
Images are built
Images are scanned
Images are pushed to DockerHub
Kustomize image tags are updated
ArgoCD deploys the new version
Notification is sent
```

---

## 23. Manual Kubernetes deployment for testing

If you want to test without ArgoCD:

```bash
kubectl apply -k k8s/overlays/prod
```

Check:

```bash
kubectl -n devconnect get pods
```

Delete manual deployment:

```bash
kubectl delete -k k8s/overlays/prod
```

For the full project, use ArgoCD instead of manual `kubectl apply`.

---

## 24. Useful access commands

A helper script prints port-forward commands:

```bash
./scripts/06-port-forward-cheatsheet.sh
```

Common commands:

```bash
# App
kubectl -n devconnect port-forward svc/frontend 3000:80

# ArgoCD
kubectl -n argocd port-forward svc/argocd-server 8080:443

# Grafana
kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3001:80

# Prometheus
kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090

# Loki Gateway
kubectl -n monitoring port-forward svc/loki-gateway 3100:80
```

---

## 25. Troubleshooting guide

### GitHub Actions fails at DockerHub login

Check:

```text
DOCKERHUB_TOKEN exists
DockerHub token is valid
DockerHub username is bongodev
Repository has Actions enabled
```

### GitHub Actions cannot commit GitOps update

Check:

```text
Repository → Settings → Actions → General → Workflow permissions
```

Set:

```text
Read and write permissions
```

If the branch is protected, allow GitHub Actions or use a Personal Access Token.

### Trivy or OWASP fails

This means vulnerabilities were found. For teaching:

- open the GitHub Actions log,
- read the vulnerable package/image,
- update dependencies or base images,
- rerun the workflow.

For live demos, you can temporarily change severity policy, but for real learning keep the gate strict.

### SonarQube scan is skipped

This is expected if these secrets are not set:

```text
SONAR_TOKEN
SONAR_HOST_URL
```

### ImagePullBackOff in Kubernetes

Run:

```bash
kubectl -n devconnect describe pod <pod-name>
```

Common causes:

```text
Image tag does not exist in DockerHub
DockerHub image is private
Wrong image name
GitHub Actions did not push images
Kustomization tag was not updated
```

Check DockerHub image name:

```text
bongodev/devconnect-<service>:<git-sha>
```

### ArgoCD is OutOfSync

Run:

```bash
kubectl -n argocd get applications
kubectl -n argocd describe application devconnect
```

Common causes:

```text
Invalid YAML
Wrong repository URL
Private repository without ArgoCD credentials
Wrong branch
Kustomize error
Image tag missing
```

### Analytics page fails

Check Analytics service:

```bash
kubectl -n devconnect logs deploy/analytics-service --tail=100
kubectl -n devconnect get pods | grep analytics
```

Check Redis:

```bash
kubectl -n devconnect exec -it statefulset/redis -- redis-cli ping
```

Expected:

```text
PONG
```

### Post is not appearing after create

Check worker logs:

```bash
kubectl -n devconnect logs deploy/worker-service -f
```

Check Redis queue:

```bash
kubectl -n devconnect exec -it statefulset/redis -- redis-cli LLEN cloudconnect:queue:post-create
```

Check post jobs in PostgreSQL:

```bash
kubectl -n devconnect exec -it statefulset/postgres -- \
  psql -U cloudconnect -d cloudconnect -c "SELECT id, status, error FROM post_jobs ORDER BY created_at DESC LIMIT 10;"
```

### ArgoCD runtime verification fails in GitHub Actions

Check these secrets:

```text
EC2_HOST
EC2_USER
EC2_SSH_PRIVATE_KEY
EC2_SSH_PORT
```

Then SSH to EC2 manually and run:

```bash
kubectl -n argocd get application devconnect
kubectl -n devconnect get pods
kubectl -n devconnect get servicemonitor
kubectl -n devconnect rollout status deployment/frontend
```

If ArgoCD is `OutOfSync`, check repository URL, branch, kustomization errors, and DockerHub image tags.

### App-level Prometheus metrics are missing

Check service endpoints:

```bash
kubectl -n devconnect exec deploy/auth-service -- \
  python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/prometheus').read().decode()[:200])"

kubectl -n devconnect exec deploy/worker-service -- \
  python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:9100/metrics').read().decode()[:200])"
```

Check ServiceMonitors:

```bash
kubectl -n devconnect get servicemonitor
kubectl -n monitoring get prometheus
```

If ServiceMonitors exist but Prometheus does not discover them, reinstall monitoring with:

```bash
./scripts/04-install-monitoring.sh
```

The values file enables cross-namespace ServiceMonitor discovery.

### Gmail notification is not sent

Check these secrets:

```text
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=<gmail-address>
SMTP_PASSWORD=<gmail-app-password>
CI_EMAIL_RECIPIENT=<recipient>
```

Also confirm the Google account has 2-Step Verification enabled and that `SMTP_PASSWORD` is an App Password.

### Grafana has no data

Check monitoring pods:

```bash
kubectl -n monitoring get pods
```

Check Prometheus targets by port-forwarding Prometheus:

```bash
kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090
```

Open:

```text
http://localhost:9090/targets
```

### Loki logs are missing

Check Alloy logs:

```bash
kubectl -n monitoring logs -l app.kubernetes.io/name=alloy --tail=100
```

Check Loki pods:

```bash
kubectl -n monitoring get pods | grep loki
```

### EC2 runs out of resources

Check:

```bash
free -h
df -h
kubectl top nodes
kubectl top pods -A
```

If the instance is small, use a larger instance or stop unnecessary workloads.

---

## 26. Cleanup

### Local cleanup

```bash
docker compose down -v
```

### Kubernetes app cleanup

```bash
kubectl delete -k k8s/overlays/prod
```

### Monitoring cleanup

```bash
helm uninstall kube-prometheus-stack -n monitoring
helm uninstall loki -n monitoring
helm uninstall alloy -n monitoring
kubectl delete namespace monitoring
```

### ArgoCD cleanup

```bash
kubectl delete namespace argocd
```

### EC2 cleanup

Terminate the EC2 instance from AWS Console when the lab is finished to avoid cost.

---

## 27. What students should submit

Students should submit screenshots or links showing:

```text
1. Local Docker Compose app running
2. Passing tests locally
3. GitHub Actions PR pipeline passing
4. DockerHub images pushed under bongodev or their own DockerHub account
5. EC2/k3s node ready
6. ArgoCD application synced and healthy
7. DevConnect pods running in Kubernetes
8. DevConnect UI working through port-forward or ingress
9. Worker processing a post job
10. Grafana dashboard running
11. Prometheus targets available
12. DevConnect app-level Prometheus metrics visible
13. cAdvisor container metrics target visible
14. Loki/Grafana logs visible
15. ArgoCD runtime verification job passing in GitHub Actions
16. bongoDev branded CI/CD success/failure email notification
```

---

## 28. Important teaching note

This project is intentionally designed as a strong DevOps learning project, not a fully managed production AWS architecture.

In a real production system, you would likely use:

```text
Amazon EKS or ECS Fargate
Amazon RDS PostgreSQL
Amazon ElastiCache Redis
AWS Secrets Manager
AWS ALB Ingress Controller
External DNS
ACM TLS certificates
Managed Grafana or Amazon Managed Prometheus/Grafana
```

For students, EC2 + k3s is easier to understand and operate while still teaching real CI/CD, Kubernetes, GitOps, security scanning, and monitoring concepts.

---

# Terraform EC2 Provisioning

You can create the EC2 machine for this project from your local machine using Terraform.

The Terraform code is included in:

```text
terraform/
```

It creates:

- Ubuntu 22.04 EC2 instance
- Default instance type: `t3.medium` for a 4 GB RAM lab machine
- 30 GB encrypted `gp3` EBS root volume
- Security group with essential ports
- Optional AWS Systems Manager access
- Basic OS packages and Kubernetes-friendly sysctl settings

## Terraform quick start

From your local machine:

```bash
cd terraform
```

Create an SSH key if you do not already have one:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/devconnect_ec2 -N "" -C "devconnect-pro"
```

Create Terraform variables:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Find your public IP:

```bash
curl https://checkip.amazonaws.com
```

Edit `terraform.tfvars` and set:

```hcl
allowed_ssh_cidr   = "YOUR_PUBLIC_IP/32"
allowed_admin_cidr = "YOUR_PUBLIC_IP/32"
```

Then run:

```bash
terraform init
terraform fmt
terraform validate
terraform plan
terraform apply
```

Terraform will output the EC2 public IP and SSH command.

## After Terraform creates EC2

SSH into the EC2 instance:

```bash
ssh -i ~/.ssh/devconnect_ec2 ubuntu@<EC2_PUBLIC_IP>
```

Then clone your repo and run the bootstrap scripts:

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

## GitHub Secrets after Terraform

Add these to GitHub Actions secrets:

```text
EC2_HOST=<EC2 public IP from terraform output>
EC2_USER=ubuntu
EC2_SSH_PORT=22
EC2_SSH_PRIVATE_KEY=<contents of ~/.ssh/devconnect_ec2>
```

Get the private key content with:

```bash
cat ~/.ssh/devconnect_ec2
```

## Default security group ports

| Port | Purpose | Source |
|---:|---|---|
| 22 | SSH | Your configured `allowed_ssh_cidr` |
| 80 | HTTP app ingress | `allowed_http_cidr` |
| 443 | HTTPS app ingress | `allowed_http_cidr` |

Optional admin ports like Grafana, ArgoCD, Prometheus, Loki, and Kubernetes API are closed by default. Use `kubectl port-forward` or SSH tunneling unless you intentionally enable them in Terraform.

## Destroy EC2 when finished

```bash
cd terraform
terraform destroy
```
