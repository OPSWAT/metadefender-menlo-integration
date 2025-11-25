#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures
set -x  # Print commands as they execute (verbose mode)

CWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd );
cd $CWD/..

COMMIT_HASH="%build.vcs.number%"
echo "##teamcity[setParameter name='env.BITBUCKET_COMMIT_HASH' value='$COMMIT_HASH']"

export VERSION=m_`git rev-parse --short HEAD`
DOCKER_IMAGE=${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/opswat/mdcl-menlo:${ENVIRONMENT}-$VERSION

# Set TeamCity parameter for Docker image (matches env.DOCKER_IMAGE_MENLO_us-west-2 in TeamCity config)
echo "##teamcity[setParameter name='env.DOCKER_IMAGE_MENLO_us-west-2' value='${DOCKER_IMAGE}']"

echo "Attempting to build image $DOCKER_IMAGE"

cd ./kubernetes

# Login to ECR using AWS CLI
echo "Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Check if image exists in ECR using AWS CLI
echo "Checking if image exists in ECR: $DOCKER_IMAGE"
REPO_NAME="opswat/mdcl-menlo"
IMAGE_TAG="${ENVIRONMENT}-${VERSION}"  # e.g., dev-m_790ce64

if aws ecr describe-images --repository-name $REPO_NAME --image-ids imageTag=$IMAGE_TAG --region ${AWS_REGION} &> /dev/null; then
    echo "Image already exists in ECR: $DOCKER_IMAGE"
    echo "Skipping build and push"
else
    echo "Image does not exist in ECR, building and pushing..."
    
    # Build the Docker image
    echo "Building Docker image: $DOCKER_IMAGE"
    cd $CWD/..
    docker build -t $DOCKER_IMAGE .
    if [[ $? -ne 0 ]]; then
        echo "ERROR: Failed to build Docker image" >&2
        exit 1
    fi
    echo "Docker image built successfully"
    
    # Push the Docker image to ECR
    echo "Pushing Docker image to ECR: $DOCKER_IMAGE"
    docker push $DOCKER_IMAGE
    if [[ $? -ne 0 ]]; then
        echo "ERROR: Failed to push Docker image to ECR" >&2
        exit 1
    fi
    echo "Docker image pushed successfully"
    
    # Verify the image was actually pushed to ECR
    echo "Verifying image exists in ECR..."
    sleep 2  # Give ECR a moment to register the image
    if aws ecr describe-images --repository-name $REPO_NAME --image-ids imageTag=${ENVIRONMENT}-${VERSION} --region ${AWS_REGION} &> /dev/null; then
        echo "✓ Image verified in ECR: $DOCKER_IMAGE"
    else
        echo "WARNING: Image push completed but verification failed. The image may still be processing in ECR." >&2
        echo "You can verify manually with: aws ecr describe-images --repository-name $REPO_NAME --image-ids imageTag=$IMAGE_TAG --region ${AWS_REGION}" >&2
    fi
fi

exit 0
