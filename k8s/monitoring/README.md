# Monitoring Stack

This folder contains values/manifests for:

- kube-prometheus-stack: Prometheus, Grafana, Alertmanager, node-exporter, kube-state-metrics
- Loki: log storage
- Grafana Alloy: Kubernetes pod log collection to Loki
- cAdvisor: container-level resource metrics

Install with:

```bash
./scripts/04-install-monitoring.sh
```

Access Grafana locally from the EC2 machine:

```bash
kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3001:80
```

Default demo login:

```text
admin / admin123
```
