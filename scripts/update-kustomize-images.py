#!/usr/bin/env python3
"""Update all DevConnect image tags in k8s/overlays/prod/kustomization.yaml."""
from __future__ import annotations

import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("Usage: update-kustomize-images.py <new-tag>")

new_tag = sys.argv[1]
path = Path("k8s/overlays/prod/kustomization.yaml")
text = path.read_text()

images = [
    "bongodev/devconnect-frontend",
    "bongodev/devconnect-auth-service",
    "bongodev/devconnect-user-service",
    "bongodev/devconnect-post-service",
    "bongodev/devconnect-like-service",
    "bongodev/devconnect-comment-service",
    "bongodev/devconnect-analytics-service",
    "bongodev/devconnect-worker-service",
]

for image in images:
    pattern = rf"(name:\s*{re.escape(image)}\n\s*newTag:\s*)([^\n]+)"
    text, count = re.subn(pattern, rf"\g<1>{new_tag}", text)
    if count != 1:
        raise SystemExit(f"Could not update image tag for {image}")

path.write_text(text)
print(f"Updated DevConnect image tags to {new_tag}")
