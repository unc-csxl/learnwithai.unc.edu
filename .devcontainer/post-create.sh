#!/usr/bin/env bash
set -euo pipefail

sudo mkdir -p /home/vscode/.cache/uv /home/vscode/.pub-cache
sudo chown -R vscode:vscode /home/vscode/.cache /home/vscode/.pub-cache

cd /workspaces/learnwithai

uv sync --all-packages --all-groups

if [ -f "client/pubspec.yaml" ]; then
  (cd client && flutter pub get)
fi