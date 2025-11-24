#!/bin/bash
set -euo pipefail

# Usage:
#
# export AWS_ACCESS_KEY_ID=?
# export AWS_ACCOUNT=?
# export AWS_REGION=us-west-2
# export AWS_SECRET_ACCESS_KEY=?
# export ARGOCD_SERVER=?
# export ARGOCD_APP_NAME=?
# export ENVIRONMENT=?
# export VERSION=? (optional, defaults to git short hash)
#
# ./tc-ci/deploy-argocd.sh

CWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd );
cd $CWD/..

# Install required tools (kubectl and argocd)
source ./tc-ci/install-tools.sh

# Check for AWS CLI
if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI is not installed or not in PATH" >&2
    echo "Please install AWS CLI to continue with deployment." >&2
    exit 1
fi

# Set version if not provided
if [[ -z "${VERSION:-}" ]]; then
    export VERSION=m_`git rev-parse --short HEAD`
fi

DOCKER_IMAGE=${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/opswat/mdcl-menlo:${ENVIRONMENT}-$VERSION

echo "Attempting to deploy image $DOCKER_IMAGE to ArgoCD"

# Validate required environment variables
if [[ -z "${ARGOCD_SERVER:-}" ]]; then
    echo "ERROR: ARGOCD_SERVER environment variable is not set" >&2
    echo "Please set ARGOCD_SERVER before deploying. Example:" >&2
    echo "  export ARGOCD_SERVER=argocd.example.com" >&2
    exit 1
fi

if [[ -z "${ARGOCD_APP_NAME:-}" ]]; then
    echo "ERROR: ARGOCD_APP_NAME environment variable is not set" >&2
    echo "Please set ARGOCD_APP_NAME before deploying. Example:" >&2
    echo "  export ARGOCD_APP_NAME=metadefender-menlo-dev" >&2
    exit 1
fi

cd ./kubernetes

# Login to ECR
echo "Logging into ECR..."
./deploy.aws.sh ecr_login

# Verify image exists in ECR
echo "Verifying image exists in ECR: $DOCKER_IMAGE"
if ! ./deploy.aws.sh inspect &> /dev/null; then
    echo "ERROR: Image $DOCKER_IMAGE does not exist in ECR!" >&2
    echo "Please build and push the image first using: ./tc-ci/build.sh" >&2
    echo "" >&2
    echo "The image should be built and pushed before deploying to ArgoCD." >&2
    echo "Make sure Step 1 includes building the Docker image, or add a separate build step." >&2
    exit 1
fi

echo "Image verified in ECR: $DOCKER_IMAGE"
echo "Note: ArgoCD will pull the image directly from ECR, no local pull needed."

# Login to ArgoCD (if not already logged in)
echo "Checking ArgoCD login status..."
if ! argocd account get-user-info --server $ARGOCD_SERVER &> /dev/null; then
    echo "Not logged in to ArgoCD. Please login:" >&2
    echo "  argocd login $ARGOCD_SERVER" >&2
    exit 1
fi

# Check if ArgoCD application exists
echo "Checking if ArgoCD application '$ARGOCD_APP_NAME' exists..."
if ! argocd app get $ARGOCD_APP_NAME --server $ARGOCD_SERVER &> /dev/null; then
    echo "ERROR: ArgoCD application '$ARGOCD_APP_NAME' does not exist!" >&2
    echo "Please create the application first or check the application name." >&2
    exit 1
fi

# Sync ArgoCD application
echo "Syncing ArgoCD application '$ARGOCD_APP_NAME'..."
argocd app sync $ARGOCD_APP_NAME --server $ARGOCD_SERVER --prune

# Wait for sync to complete
echo "Waiting for sync to complete..."
argocd app wait $ARGOCD_APP_NAME --server $ARGOCD_SERVER --timeout 300

# Get application status
echo ""
echo "ArgoCD application status:"
argocd app get $ARGOCD_APP_NAME --server $ARGOCD_SERVER

echo ""
echo "Deployment to ArgoCD completed successfully!"
echo "Image deployed: $DOCKER_IMAGE"

