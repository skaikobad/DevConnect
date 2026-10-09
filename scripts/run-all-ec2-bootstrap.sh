#!/usr/bin/env bash
set -euo pipefail

: "${REPO_URL:?Set REPO_URL=https://github.com/<org>/<repo>.git first}"

./scripts/01-install-docker.sh
./scripts/02-install-k3s.sh
./scripts/03-install-argocd.sh
./scripts/04-install-monitoring.sh
./scripts/05-bootstrap-devconnect.sh
