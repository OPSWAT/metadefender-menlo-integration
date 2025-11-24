#!/bin/bash
set -euo pipefail

# Usage:
#
# export AWS_ACCESS_KEY_ID=?
# export AWS_ACCOUNT=?
# export AWS_REGION=us-west-2
# export AWS_SECRET_ACCESS_KEY=?
# export CDR_WORKFLOW=false
# export CERTIFICATE_ARN=arn:aws:acm:us-west-2:108895011981:certificate/953cdfcd-849e-47b9-a703-f83f8fb0947e
# export ENVIRONMENT=?
# export EKS_CLUSTER=dev-mdc-menlo-usw2
# export MENLO_MD_KAFKA_CLIENT_ID=menloPlugin
# export MENLO_MD_KAFKA_ENABLED=true
# export MENLO_MD_KAFKA_SERVER=?
# export MENLO_MD_KAFKA_SSL=true
# export MENLO_MD_KAFKA_TOPIC=dev_menlo_middleware
# export MENLO_MD_SENTRY_DSN=???
# export MENLO_MD_SNS_ARN=arn:aws:sns:us-west-2:108895011981:dev-mdcl-menlo
# export MENLO_MD_SNS_ENABLED=true
# export MENLO_MD_SNS_REGION=us-west-2
# export MENLO_MD_URL=https://api.metadefender.com
#
# ./tc-ci/deploy.sh

CWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd );
cd $CWD/..

# Check for required tools
if ! command -v kubectl &> /dev/null; then
    echo "ERROR: kubectl is not installed or not in PATH" >&2
    echo "Please install kubectl to continue with deployment." >&2
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI is not installed or not in PATH" >&2
    echo "Please install AWS CLI to continue with deployment." >&2
    exit 1
fi

export VERSION=m_`git rev-parse --short HEAD`
DOCKER_IMAGE=${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/opswat/mdcl-menlo:${ENVIRONMENT}-$VERSION

echo "Attempting to deploy image $DOCKER_IMAGE"

if [[ $ENVIRONMENT == "dev" ]]; then
    export MENLO_MD_URL=${MENLO_MD_URL}
fi

if [[ $CDR_WORKFLOW == "true" ]]; then
    if [[ $ENVIRONMENT == "prod" ]]; then
        export EKS_NAMESPACE=${ENVIRONMENT}-mdc-menlo-cdr
    else
        export EKS_NAMESPACE=${ENVIRONMENT}-mdc-menlo
    fi
    export MENLO_MD_MDCLOUD_RULE="cdr"
else 
    export EKS_NAMESPACE=${ENVIRONMENT}-mdc-menlo
    export MENLO_MD_MDCLOUD_RULE="multiscan, sanitize, unarchive"
fi

cd ./kubernetes

./deploy.aws.sh ecr_login

./deploy.aws.sh inspect
if [[ $? -ne 0 ]]; then
    echo "Image $DOCKER_IMAGE does not exist. Please build the image first!"
    exit 1
fi

./deploy.aws.sh configure_cluster

if ! kubectl get namespace $EKS_NAMESPACE &> /dev/null; then
    echo "Namespace $EKS_NAMESPACE does not exist, creating it..."
    kubectl create namespace $EKS_NAMESPACE
fi

# Validate required environment variables
if [[ -z "${CERTIFICATE_ARN:-}" ]]; then
    echo "ERROR: CERTIFICATE_ARN environment variable is not set or is empty" >&2
    echo "Please set CERTIFICATE_ARN before deploying. Example:" >&2
    echo "  export CERTIFICATE_ARN=arn:aws:acm:us-west-2:123456789012:certificate/abc123..." >&2
    exit 1
fi

# Validate that CERTIFICATE_ARN looks like a valid ARN
if [[ ! "${CERTIFICATE_ARN}" =~ ^arn:aws:acm: ]]; then
    echo "WARNING: CERTIFICATE_ARN does not appear to be a valid ACM certificate ARN" >&2
    echo "CERTIFICATE_ARN value: ${CERTIFICATE_ARN}" >&2
    echo "Expected format: arn:aws:acm:REGION:ACCOUNT:certificate/ID" >&2
    # Don't exit here, just warn - let Kubernetes validation catch it if it's truly invalid
fi

envsubst < deployment.yaml > deployment.yaml.tmp && mv deployment.yaml.tmp deployment.yaml
envsubst < ingress.yaml > ingress.yaml.tmp && mv ingress.yaml.tmp ingress.yaml

./deploy.aws.sh apply_deployment

./deploy.aws.sh apply_service

./deploy.aws.sh apply_ingress

if [[ $ENVIRONMENT == "prod" ]]; then 
    ./deploy.aws.sh apply_hpa
fi

echo "Deployment completed successfully!"
