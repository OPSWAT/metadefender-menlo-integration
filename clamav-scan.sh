#!/usr/bin/env bash

set -e 
set -x 

ARTIFACTS_DIR="./artifacts"  # Directory to store the reports
mkdir -p "${ARTIFACTS_DIR}"   # Create artifacts directory if it doesn't exist

CWD=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd $CWD

# Get version from git if not set
export VERSION=${VERSION:-m_$(git rev-parse --short HEAD)}
DOCKER_IMAGE=${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/opswat/mdcl-menlo:${ENVIRONMENT}-$VERSION

REPORT_FILE="/var/log/clamav_scan_report.txt"

echo "##teamcity[progressMessage 'Processing malware scan']"
echo "Using Docker image: $DOCKER_IMAGE"

# Login to ECR
echo "##teamcity[blockOpened name='ECR Login']"
cd ./kubernetes
./deploy.aws.sh ecr_login
cd ..
echo "##teamcity[blockClosed name='ECR Login']"

# Pull the Docker image from ECR
echo "##teamcity[blockOpened name='Pull Image']"
echo "Pulling Docker image from ECR..."
if ! docker pull "$DOCKER_IMAGE"; then
    echo "ERROR: Failed to pull Docker image ${DOCKER_IMAGE}."
    echo "This may indicate the image hasn't been built yet or doesn't exist in ECR."
    exit 1
fi
echo "Successfully pulled Docker image ${DOCKER_IMAGE}"
echo "##teamcity[blockClosed name='Pull Image']"

# Run ClamAV scan
echo "##teamcity[blockOpened name='Run ClamAV Scan']"
echo "Running Docker container for ClamAV scan..."

# Check if the container already exists and remove it if it does
CONTAINER_NAME="temp_menlo_clamav"
if [[ $(docker ps -aq -f name="${CONTAINER_NAME}") ]]; then
    echo "Removing existing container ${CONTAINER_NAME}..."
    docker rm -f "${CONTAINER_NAME}"
fi

# Run container: install ClamAV, mount start.sh, and run scan
CONTAINER_ID=$(docker run -d --name "${CONTAINER_NAME}" \
    -v "$(pwd)/start.sh:/usr/src/app/start.sh:ro" \
    "$DOCKER_IMAGE" sh -c "
        apk add --no-cache clamav clamav-libunrar && \
        freshclam && \
        chmod +x /usr/src/app/start.sh && \
        /usr/src/app/start.sh
    ")

# Wait for the container to finish
EXIT_CODE=$(docker wait "${CONTAINER_ID}")

# Copy the ClamAV report to the artifacts directory
docker cp "${CONTAINER_ID}:${REPORT_FILE}" "${ARTIFACTS_DIR}/"

echo "ClamAV report copied to ${ARTIFACTS_DIR}/clamav_scan_report.txt"

# Clean up the container
docker rm -f "${CONTAINER_ID}"
echo "##teamcity[blockClosed name='Run ClamAV Scan']"

# Publish artifacts to TeamCity
echo "##teamcity[publishArtifacts '${ARTIFACTS_DIR} => .']"
echo "ClamAV scan completed. Report available in ${ARTIFACTS_DIR}/"


