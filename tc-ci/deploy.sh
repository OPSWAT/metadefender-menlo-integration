#!/bin/bash

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

export VERSION=m_`git rev-parse --short HEAD`
DOCKER_IMAGE=${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/mdcl-menlo:${ENVIRONMENT}-$VERSION

echo "Attempting to deploy image $DOCKER_IMAGE"

if [[ $ENVIRONMENT == "dev" ]]; then
    export MENLO_MD_URL=${MENLO_MD_URL}
fi

if [[ $CDR_WORKFLOW == "true" ]]; then
    if [[ $ENVIRONMENT == "prod" ]]; then
        export EKS_NAMESPACE=menlo-${ENVIRONMENT}-cdr
    else
        export EKS_NAMESPACE=menlo-${ENVIRONMENT}
    fi
    export MENLO_MD_MDCLOUD_RULE="cdr"
else 
    export EKS_NAMESPACE=menlo-${ENVIRONMENT}
    export MENLO_MD_MDCLOUD_RULE="multiscan, sanitize, unarchive"
fi

cd ./kubernetes

./deploy.aws.sh ecr_login
[[ $? -ne 0 ]] && exit $?

./deploy.aws.sh inspect
if [[ $? -ne 0 ]]; then
    echo "Image $DOCKER_IMAGE does not exist. Please build the image first!"
    exit 1
fi

./deploy.aws.sh configure_cluster
[[ $? -ne 0 ]] && exit $?

kubectl get namespace $EKS_NAMESPACE || kubectl create namespace $EKS_NAMESPACE
[[ $? -ne 0 ]] && exit $?

envsubst < deployment.yaml > deployment.yaml.tmp && mv deployment.yaml.tmp deployment.yaml
envsubst < ingress.yaml > ingress.yaml.tmp && mv ingress.yaml.tmp ingress.yaml

./deploy.aws.sh apply_deployment
[[ $? -ne 0 ]] && exit $?

./deploy.aws.sh apply_service
[[ $? -ne 0 ]] && exit $?

./deploy.aws.sh apply_ingress
[[ $? -ne 0 ]] && exit $?

if [[ $ENVIRONMENT == "prod" ]]; then 
    ./deploy.aws.sh apply_hpa
    [[ $? -ne 0 ]] && exit $?
fi

exit 0