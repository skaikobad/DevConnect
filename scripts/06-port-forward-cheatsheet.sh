#!/usr/bin/env bash
set -euo pipefail
cat <<'INFO'
Useful port-forward commands:

DevConnect frontend:
  kubectl -n devconnect port-forward svc/frontend 3000:80

ArgoCD:
  kubectl -n argocd port-forward svc/argocd-server 8080:443

Grafana:
  kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3001:80

Prometheus:
  kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090

Loki Gateway:
  kubectl -n monitoring port-forward svc/loki-gateway 3100:80
INFO
