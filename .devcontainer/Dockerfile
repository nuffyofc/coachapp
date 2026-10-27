FROM mcr.microsoft.com/devcontainers/python:3.12

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Azure CLI + Bicep installed later via features or postCreate as needed.
WORKDIR /workspace
