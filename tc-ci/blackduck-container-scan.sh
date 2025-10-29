#!/bin/bash
CWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd );
cd $CWD/..

BLACKDUCK_URL="https://opswat.blackducksoftware.com/"
export VERSION=m_"$(git rev-parse --short HEAD)"
DOCKER_IMAGE=${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/opswat/mdcl-menlo:${ENVIRONMENT}-$VERSION
BD_PARENT_PROJECT="MD Cloud Menlo Container"

BRANCH_NAME="$(git branch --show-current 2>/dev/null)"
if [[ -z "$BRANCH_NAME" ]]; then
    # Detached HEAD - try to get tag name
    BRANCH_NAME="$(git describe --tags --exact-match 2>/dev/null)"
    if [[ -z "$BRANCH_NAME" ]]; then
        # Last resort - use commit SHA
        BRANCH_NAME="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
        echo "WARNING: Not on a branch or tag, using commit SHA: $BRANCH_NAME"
    else
        echo "Detected tag in detached HEAD: $BRANCH_NAME"
    fi
fi


echo "Attempting to scan image $DOCKER_IMAGE"

cd ./kubernetes
./deploy.aws.sh ecr_login
cd ../
BD_PROJECT_VERSION=""
BD_VERSION_PHASE=""

case "$BRANCH_NAME" in
    develop)
        BD_PROJECT_VERSION="main"
        BLACKDUCK_VERSION_PHASE="DEVELOPMENT"
        echo "Detected development branch ($BRANCH_NAME) → version: main"
        ;;
    main)
        BD_PROJECT_VERSION="customer"
        BLACKDUCK_VERSION_PHASE="RELEASED"
        echo "Warning: deployment branch ($BRANCH_NAME) without tag → version: deployment"
        ;;
    release/*|hotfix/*)
        BD_PROJECT_VERSION="${BRANCH_NAME}"
        BLACKDUCK_VERSION_PHASE="PRERELEASE"
        echo "Detected release/hotfix branch → version: $BRANCH_NAME (PRERELEASE)"
        ;;
    feature/*)
        BD_PROJECT_VERSION="${BRANCH_NAME}"
        BLACKDUCK_VERSION_PHASE="DEVELOPMENT"
        echo "Detected feature branch → version: $BRANCH_NAME"
        ;;
    [0-9]*)
        BD_PROJECT_VERSION="v${BRANCH_NAME}"
        BLACKDUCK_VERSION_PHASE="RELEASED"
        echo "Detected version tag branch ($BRANCH_NAME) → version: v${BRANCH_NAME}"
        ;;
    *)
        BD_PROJECT_VERSION="${BRANCH_NAME}"
        BLACKDUCK_VERSION_PHASE="DEVELOPMENT"
        echo "Using branch name as version: $BRANCH_NAME"
        ;;
esac

echo "Black Duck Version: $BD_PROJECT_VERSION"
echo "Black Duck Phase: $BLACKDUCK_VERSION_PHASE"

echo "##teamcity[blockOpened name='Docker Image Preparation']"
echo "##teamcity[blockOpened name='Pulling Docker Image']"

echo "Pulling Docker image from ECR..."
if ! docker pull "$DOCKER_IMAGE"; then
    echo "Failed to pull image: $DOCKER_IMAGE"
    exit 1
fi
echo "##teamcity[blockClosed name='Pulling Docker Image']"

IMAGE_TAR_FILE="/tmp/docker_image_$(date +%s).tar"

echo "Saving Docker image to $IMAGE_TAR_FILE..."
if ! docker save "$DOCKER_IMAGE" > "$IMAGE_TAR_FILE"; then
    echo "Failed to save image to tar file"
    exit 1
fi

echo "Verifying saved image..."
if ! docker load < "$IMAGE_TAR_FILE" > /dev/null 2>&1; then
    echo "Error verifying saved image."
    rm -f "$IMAGE_TAR_FILE"
    exit 1
fi

echo "##teamcity[blockClosed name='Docker Image Preparation']"

echo "##teamcity[blockOpened name='Download Synopsys']"
echo "Downloading Synopsys Detect script..."
if ! curl -O https://detect.blackduck.com/detect10.sh; then
    echo "Failed to download Synopsys Detect script. Exiting."
    rm -f "$IMAGE_TAR_FILE"
    exit 1
fi
chmod +x detect10.sh

echo "##teamcity[blockClosed name='Download Synopsys']"
echo "##teamcity[blockOpened name='BlackDuck Container Scan']"

./detect10.sh \
    --blackduck.url="$BLACKDUCK_URL" \
    --blackduck.api.token="$BD_TOKEN" \
    --detect.project.name="$BD_PARENT_PROJECT" \
    --detect.project.version.name="$BD_PROJECT_VERSION" \
    --detect.project.version.phase="$BLACKDUCK_VERSION_PHASE" \
    --detect.container.scan.file.path="$IMAGE_TAR_FILE" \
    --detect.tools=CONTAINER_SCAN \
    --detect.tools.excluded=BINARY_SCAN \
    --detect.blackduck.signature.scanner.memory=8192 \
    --detect.project.version.distribution=SAAS \
    --detect.blackduck.signature.scanner.jvm.additional.options="-XX:+UseG1GC" \
    --logging.level.com.synopsys.integration=DEBUG

detect_exit_code="$?"
if [[ "$detect_exit_code" != "0" ]]; then
    echo "Detect script failed for image: $DOCKER_IMAGE with exit code: $detect_exit_code"
    rm -f "$IMAGE_TAR_FILE"
    echo "##teamcity[blockClosed name='BlackDuck Container Scan']"
    exit 1
fi

rm -f "$IMAGE_TAR_FILE"

echo "##teamcity[blockClosed name='BlackDuck Container Scan']"
echo "Scan complete."