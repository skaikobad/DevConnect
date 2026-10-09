#!/usr/bin/env bash
set -euo pipefail

if ! command -v helm >/dev/null 2>&1; then
  curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  -f k8s/monitoring/kube-prometheus-stack-values.yaml

helm upgrade --install loki grafana/loki \
  --namespace monitoring \
  -f k8s/monitoring/loki-values.yaml

helm upgrade --install alloy grafana/alloy \
  --namespace monitoring \
  -f k8s/monitoring/alloy-values.yaml 

kubectl apply -f k8s/monitoring/cadvisor-daemonset.yaml

printf '\nMonitoring installed. Grafana port-forward:\n'
printf 'kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3001:80\n'
printf 'Login: admin / admin123\n'