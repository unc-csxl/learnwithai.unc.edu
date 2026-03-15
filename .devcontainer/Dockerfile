FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

ARG DEBIAN_FRONTEND=noninteractive
ARG FLUTTER_VERSION=stable

# Core OS packages, Python tooling, Java, and Linux deps useful for Flutter web/Linux work
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    build-essential \
    ca-certificates \
    clang \
    cmake \
    curl \
    git \
    gnupg \
    jq \
    libgtk-3-dev \
    libstdc++-12-dev \
    make \
    ninja-build \
    openjdk-17-jdk \
    pkg-config \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    unzip \
    xz-utils \
    zip \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh

# Install Flutter SDK
RUN git clone https://github.com/flutter/flutter.git /usr/local/flutter -b ${FLUTTER_VERSION}
ENV FLUTTER_HOME=/usr/local/flutter
ENV PATH="/usr/local/flutter/bin:/home/vscode/.local/bin:${PATH}"

# Let the vscode user own caches and SDK-adjacent writable locations used during development
RUN mkdir -p /home/vscode/.pub-cache \
    && chown -R vscode:vscode /home/vscode/.pub-cache /usr/local/flutter

USER vscode
WORKDIR /workspaces/learnwithai

# Warm up Flutter and Dart tooling
RUN flutter config --no-analytics \
    && dart --disable-analytics \
    && flutter doctor