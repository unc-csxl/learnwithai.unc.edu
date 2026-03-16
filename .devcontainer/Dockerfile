FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

ARG DEBIAN_FRONTEND=noninteractive
ARG NODE_MAJOR=24

# Core OS packages and Python tooling
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    build-essential \
    ca-certificates \
    curl \
    git \
    gnupg \
    jq \
    make \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    unzip \
    zip \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js LTS via NodeSource
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_MAJOR}.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g npm@latest \
    && corepack enable

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh

ENV PATH="/home/vscode/.local/bin:${PATH}"

USER vscode
WORKDIR /workspaces/learnwithai