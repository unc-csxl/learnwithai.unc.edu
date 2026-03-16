#!/usr/bin/env bash
set -euo pipefail

sudo mkdir -p /home/vscode/.cache/uv /home/vscode/.npm
sudo chown -R vscode:vscode /home/vscode/.cache /home/vscode/.npm

cd /workspaces/learnwithai

uv sync --all-packages --all-groups

if [ -f "frontend/package.json" ]; then
  (cd frontend && npm install)
fi