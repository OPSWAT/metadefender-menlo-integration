#!/bin/bash

# Usage:
#
# export AWS_ACCOUNT=?
# export AWS_REGION=?
# export ENVIRONMENT=?
#
# ./tc-ci/build.sh

CWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd );
cd $CWD/..

COMMIT_HASH="%build.vcs.number%"
echo "##teamcity[setParameter name='env.BITBUCKET_COMMIT_HASH' value='$COMMIT_HASH']"

export VERSION=m_`git rev-parse --short HEAD`
DOCKER_IMAGE=${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/opswat/mdcl-menlo:${ENVIRONMENT}-$VERSION

echo "Attempting to build image $DOCKER_IMAGE"

cd ./kubernetes

./deploy.aws.sh ecr_login

# Check if image exists in ECR
echo "Checking if image exists in ECR..."
if ./deploy.aws.sh inspect &> /dev/null; then
    echo "Image already exists in ECR: $DOCKER_IMAGE"
    echo "Skipping build and push"
else
    echo "Image does not exist in ECR, building and pushing..."
    ./deploy.aws.sh build_image
    if [[ $? -ne 0 ]]; then
        echo "ERROR: Failed to build image" >&2
        exit 1
    fi
    
    ./deploy.aws.sh push_image
    if [[ $? -ne 0 ]]; then
        echo "ERROR: Failed to push image" >&2
        exit 1
    fi
    
    echo "Successfully built and pushed image: $DOCKER_IMAGE"
fi

exit 0
