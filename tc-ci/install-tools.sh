#!/bin/bash
set -euo pipefail

# Install kubectl and ArgoCD CLI
# This script can be run directly in TeamCity as Step 1
# It is idempotent - it will skip installation if tools are already installed

# Check for required dependencies
if ! command -v curl &> /dev/null; then
    echo "ERROR: curl is required but not installed" >&2
    echo "Please install curl to continue." >&2
    exit 1
fi

# Install kubectl if not already present
echo "##teamcity[blockOpened name='Install kubectl']"

# Check if kubectl is already installed
if command -v kubectl &> /dev/null; then
    KUBECTL_VERSION=$(kubectl version --client --short 2>/dev/null | cut -d' ' -f3 || echo "unknown")
    echo "kubectl is already installed: $KUBECTL_VERSION"
else
    # Check if kubectl exists in common locations but not in PATH
    if [ -f "$HOME/bin/kubectl" ]; then
        if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
            export PATH="$HOME/bin:$PATH"
            echo "Added $HOME/bin to PATH for kubectl"
        fi
    elif [ -f "/usr/local/bin/kubectl" ]; then
        if [[ ":$PATH:" != *":/usr/local/bin:"* ]]; then
            export PATH="/usr/local/bin:$PATH"
        fi
    fi
    
    # Check again after PATH update
    if ! command -v kubectl &> /dev/null; then
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

        echo "Downloading kubectl from: $DOWNLOAD_URL"
        curl -LO "$DOWNLOAD_URL" || {
            echo "ERROR: Failed to download kubectl" >&2
            exit 1
        }

        # Make it executable
        chmod +x kubectl

        # Try to install to user-writable directory first (for CI environments)
        if [ -w "$HOME/bin" ] || mkdir -p "$HOME/bin" 2>/dev/null; then
            INSTALL_DIR="$HOME/bin"
            mv kubectl "$INSTALL_DIR/kubectl" || {
                echo "ERROR: Failed to install kubectl to $INSTALL_DIR" >&2
                exit 1
            }
            # Add to PATH if not already there
            if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
                export PATH="$HOME/bin:$PATH"
            fi
        elif [ -w "/usr/local/bin" ]; then
            INSTALL_DIR="/usr/local/bin"
            mv kubectl "$INSTALL_DIR/kubectl" || {
                echo "ERROR: Failed to install kubectl to $INSTALL_DIR" >&2
                exit 1
            }
        else
            # Last resort: install to current directory's bin folder
            INSTALL_DIR="$(pwd)/bin"
            mkdir -p "$INSTALL_DIR"
            mv kubectl "$INSTALL_DIR/kubectl" || {
                echo "ERROR: Failed to install kubectl to $INSTALL_DIR" >&2
                exit 1
            }
            # Add to PATH if not already there
            if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
                export PATH="$INSTALL_DIR:$PATH"
            fi
        fi
        
        echo "Installed kubectl to: $INSTALL_DIR/kubectl"

        # Verify installation
        if command -v kubectl &> /dev/null; then
            INSTALLED_VERSION=$(kubectl version --client --short 2>/dev/null | cut -d' ' -f3 || echo "unknown")
            echo "Successfully installed kubectl: $INSTALLED_VERSION"
            echo "kubectl is available at: $(command -v kubectl)"
        else
            echo "ERROR: kubectl installation verification failed" >&2
            exit 1
        fi
    else
        KUBECTL_VERSION=$(kubectl version --client --short 2>/dev/null | cut -d' ' -f3 || echo "unknown")
        echo "kubectl found in PATH: $KUBECTL_VERSION"
    fi
fi

echo "##teamcity[blockClosed name='Install kubectl']"

# Install ArgoCD CLI if not already present
echo "##teamcity[blockOpened name='Install ArgoCD CLI']"

# Check if argocd is already installed
if command -v argocd &> /dev/null; then
    ARGOCD_VERSION=$(argocd version --client --short 2>/dev/null | head -n1 | cut -d' ' -f2 || echo "unknown")
    echo "argocd is already installed: $ARGOCD_VERSION"
else
    # Check if argocd exists in common locations but not in PATH
    if [ -f "$HOME/bin/argocd" ]; then
        if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
            export PATH="$HOME/bin:$PATH"
            echo "Added $HOME/bin to PATH for argocd"
        fi
    elif [ -f "/usr/local/bin/argocd" ]; then
        if [[ ":$PATH:" != *":/usr/local/bin:"* ]]; then
            export PATH="/usr/local/bin:$PATH"
        fi
    fi
    
    # Check again after PATH update
    if ! command -v argocd &> /dev/null; then
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

        echo "Downloading argocd from: $DOWNLOAD_URL"
        curl -LO "$DOWNLOAD_URL" || {
            echo "ERROR: Failed to download argocd" >&2
            exit 1
        }

        # Make it executable
        chmod +x argocd-${OS}-${ARCH}

        # Try to install to user-writable directory first (for CI environments)
        if [ -w "$HOME/bin" ] || mkdir -p "$HOME/bin" 2>/dev/null; then
            INSTALL_DIR="$HOME/bin"
            mv argocd-${OS}-${ARCH} "$INSTALL_DIR/argocd" || {
                echo "ERROR: Failed to install argocd to $INSTALL_DIR" >&2
                exit 1
            }
            # Add to PATH if not already there
            if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
                export PATH="$HOME/bin:$PATH"
            fi
        elif [ -w "/usr/local/bin" ]; then
            INSTALL_DIR="/usr/local/bin"
            mv argocd-${OS}-${ARCH} "$INSTALL_DIR/argocd" || {
                echo "ERROR: Failed to install argocd to $INSTALL_DIR" >&2
                exit 1
            }
        else
            # Last resort: install to current directory's bin folder
            INSTALL_DIR="$(pwd)/bin"
            mkdir -p "$INSTALL_DIR"
            mv argocd-${OS}-${ARCH} "$INSTALL_DIR/argocd" || {
                echo "ERROR: Failed to install argocd to $INSTALL_DIR" >&2
                exit 1
            }
            # Add to PATH if not already there
            if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
                export PATH="$INSTALL_DIR:$PATH"
            fi
        fi
        
        echo "Installed argocd to: $INSTALL_DIR/argocd"

        # Verify installation
        if command -v argocd &> /dev/null; then
            INSTALLED_VERSION=$(argocd version --client --short 2>/dev/null | head -n1 | cut -d' ' -f2 || echo "unknown")
            echo "Successfully installed argocd: $INSTALLED_VERSION"
            echo "argocd is available at: $(command -v argocd)"
        else
            echo "ERROR: argocd installation verification failed" >&2
            exit 1
        fi
    else
        ARGOCD_VERSION=$(argocd version --client --short 2>/dev/null | head -n1 | cut -d' ' -f2 || echo "unknown")
        echo "argocd found in PATH: $ARGOCD_VERSION"
    fi
fi

echo "##teamcity[blockClosed name='Install ArgoCD CLI']"

echo ""
echo "All required tools installed successfully!"
echo "kubectl: $(command -v kubectl 2>/dev/null || echo 'not found')"
echo "argocd: $(command -v argocd 2>/dev/null || echo 'not found')"
