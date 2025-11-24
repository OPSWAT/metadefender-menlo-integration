#!/bin/bash
set -euo pipefail

# Install kubectl if not already present
# This script is idempotent - it will skip installation if kubectl is already installed

echo "##teamcity[blockOpened name='Install kubectl']"

# Check if kubectl is already installed
if command -v kubectl &> /dev/null; then
    KUBECTL_VERSION=$(kubectl version --client --short 2>/dev/null | cut -d' ' -f3 || echo "unknown")
    echo "kubectl is already installed: $KUBECTL_VERSION"
    echo "##teamcity[blockClosed name='Install kubectl']"
    exit 0
fi

echo "kubectl not found, installing..."

# Detect OS
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

# Normalize architecture
case "$ARCH" in
    x86_64)
        ARCH="amd64"
        ;;
    aarch64|arm64)
        ARCH="arm64"
        ;;
    *)
        echo "ERROR: Unsupported architecture: $ARCH" >&2
        exit 1
        ;;
esac

# Set kubectl version (use latest stable or specific version)
KUBECTL_VERSION="${KUBECTL_VERSION:-latest}"

if [ "$KUBECTL_VERSION" = "latest" ]; then
    # Get latest stable version
    KUBECTL_VERSION=$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)
    echo "Installing latest kubectl version: $KUBECTL_VERSION"
else
    echo "Installing kubectl version: $KUBECTL_VERSION"
fi

# Download kubectl
DOWNLOAD_URL="https://storage.googleapis.com/kubernetes-release/release/${KUBECTL_VERSION}/bin/${OS}/${ARCH}/kubectl"
INSTALL_DIR="${KUBECTL_INSTALL_DIR:-/usr/local/bin}"

echo "Downloading kubectl from: $DOWNLOAD_URL"
curl -LO "$DOWNLOAD_URL" || {
    echo "ERROR: Failed to download kubectl" >&2
    exit 1
}

# Make it executable and move to install directory
chmod +x kubectl
sudo mv kubectl "$INSTALL_DIR/kubectl" || {
    # If sudo fails, try without sudo (might be running as root)
    mv kubectl "$INSTALL_DIR/kubectl" || {
        echo "ERROR: Failed to install kubectl to $INSTALL_DIR" >&2
        exit 1
    }
}

# Verify installation
if command -v kubectl &> /dev/null; then
    INSTALLED_VERSION=$(kubectl version --client --short 2>/dev/null | cut -d' ' -f3 || echo "unknown")
    echo "Successfully installed kubectl: $INSTALLED_VERSION"
    echo "kubectl is available at: $(command -v kubectl)"
else
    echo "ERROR: kubectl installation verification failed" >&2
    exit 1
fi

echo "##teamcity[blockClosed name='Install kubectl']"

