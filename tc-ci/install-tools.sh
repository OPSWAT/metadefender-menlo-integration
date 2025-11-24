#!/bin/bash

set -euo pipefail

# Install kubectl if not already present
# This script is idempotent - it will skip installation if kubectl is already installed

echo "##teamcity[blockOpened name='Install kubectl']"

# Check if kubectl is already installed
if command -v kubectl &> /dev/null; then
    KUBECTL_VERSION=$(kubectl version --client --short 2>/dev/null | cut -d' ' -f3 || echo "unknown")
    echo "kubectl is already installed: $KUBECTL_VERSION"
else
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
fi

echo "##teamcity[blockClosed name='Install kubectl']"

# Install ArgoCD CLI if not already present
# This script is idempotent - it will skip installation if argocd is already installed

echo "##teamcity[blockOpened name='Install ArgoCD CLI']"

# Check if argocd is already installed
if command -v argocd &> /dev/null; then
    ARGOCD_VERSION=$(argocd version --client --short 2>/dev/null | head -n1 | cut -d' ' -f2 || echo "unknown")
    echo "argocd is already installed: $ARGOCD_VERSION"
else
    echo "argocd not found, installing..."

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

    # Set ArgoCD version (use latest stable or specific version)
    ARGOCD_VERSION="${ARGOCD_VERSION:-v2.10.4}"

    echo "Installing ArgoCD CLI version: $ARGOCD_VERSION"

    # Download argocd
    DOWNLOAD_URL="https://github.com/argoproj/argo-cd/releases/download/${ARGOCD_VERSION}/argocd-${OS}-${ARCH}"
    INSTALL_DIR="${ARGOCD_INSTALL_DIR:-/usr/local/bin}"

    echo "Downloading argocd from: $DOWNLOAD_URL"
    curl -LO "$DOWNLOAD_URL" || {
        echo "ERROR: Failed to download argocd" >&2
        exit 1
    }

    # Make it executable and move to install directory
    chmod +x argocd-${OS}-${ARCH}
    sudo mv argocd-${OS}-${ARCH} "$INSTALL_DIR/argocd" || {
        # If sudo fails, try without sudo (might be running as root)
        mv argocd-${OS}-${ARCH} "$INSTALL_DIR/argocd" || {
            echo "ERROR: Failed to install argocd to $INSTALL_DIR" >&2
            exit 1
        }
    }

    # Verify installation
    if command -v argocd &> /dev/null; then
        INSTALLED_VERSION=$(argocd version --client --short 2>/dev/null | head -n1 | cut -d' ' -f2 || echo "unknown")
        echo "Successfully installed argocd: $INSTALLED_VERSION"
        echo "argocd is available at: $(command -v argocd)"
    else
        echo "ERROR: argocd installation verification failed" >&2
        exit 1
    fi
fi

echo "##teamcity[blockClosed name='Install ArgoCD CLI']"

