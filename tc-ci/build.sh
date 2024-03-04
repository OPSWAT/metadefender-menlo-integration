#!/bin/bash

# Usage:
#
# export AWS_ACCOUNT=?
# export AWS_REGION=?
# export VERSION=?
# export ENVIRONMENT=?
# ./build.sh

DOCKER_IMAGE=${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/mdcl-menlo:${ENVIRONMENT}-$VERSION
echo "Attempting to build image $DOCKER_IMAGE"

CWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $CWD/../kubernetes

./deploy.aws.sh ecr_login
./deploy.aws.sh inspect

if [[ $? -ne 0 ]]; then
    ./deploy.aws.sh build_image
    ./deploy.aws.sh push_image
else
    echo "Image already exists, skipping"
fi