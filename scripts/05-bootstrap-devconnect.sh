#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-}"
BRANCH="${BRANCH:-main}"

if [[ -z "$REPO_URL" ]]; then
  echo "Usage: REPO_URL=https://github.com/<org>/<repo>.git ./scripts/05-bootstrap-devconnect.sh"
  exit 1
fi

TMP_FILE="/tmp/devconnect-argocd-application.yaml"
cp k8s/argocd/devconnect-application.yaml "$TMP_FILE"
sed -i "s#https://github.com/YOUR_GITHUB_ORG/YOUR_REPO.git#${REPO_URL}#g" "$TMP_FILE"
sed -i "s#targetRevision: main#targetRevision: ${BRANCH}#g" "$TMP_FILE"

kubectl apply -f "$TMP_FILE"
kubectl -n argocd get applications
printf '\nArgoCD will now sync DevConnect from: %s\n' "$REPO_URL"
