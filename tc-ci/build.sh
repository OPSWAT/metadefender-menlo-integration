#!/bin/bash
#############################
# Builds Docker image and pushes to AWS ECR.
# Skips build if image already exists in registry.
#
# Used in: <TeamCity: ... > ... >
#
# Parameters:
# None - uses environment variables
#
# Environment Variables:
# AWS_ACCOUNT   - AWS account ID
# AWS_REGION    - AWS region (e.g., us-west-2)
# ENVIRONMENT   - Target environment (dev, staging, prod)
#############################

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
./deploy.aws.sh inspect

if [[ $? -ne 0 ]]; then
    ./deploy.aws.sh build_image
    [[ $? -ne 0 ]] && exit $?
    
    ./deploy.aws.sh push_image
    [[ $? -ne 0 ]] && exit $?
else
    echo "Image already exists, skipping"
fi

exit 0
