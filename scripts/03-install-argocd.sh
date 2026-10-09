#!/usr/bin/env bash
set -euo pipefail

kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -n argocd \
  --server-side \
  --force-conflicts \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

kubectl -n argocd rollout status deployment/argocd-server --timeout=300s

printf '\nArgoCD installed. To get the initial admin password:\n'
printf 'kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo\n'
printf '\nPort forward ArgoCD UI:\n'
printf 'kubectl -n argocd port-forward svc/argocd-server 8080:443\n'
