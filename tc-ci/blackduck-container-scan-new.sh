#!/bin/bash
CWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd );
cd $CWD/..

BLACKDUCK_URL="https://opswat.blackducksoftware.com/"
export VERSION=m_"$(git rev-parse --short HEAD)"
DOCKER_IMAGE=${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/opswat/mdcl-menlo:${ENVIRONMENT}-$VERSION
BRANCH="$(git branch --show-current)"
TAG="$(git describe --tags --exact-match 2>/dev/null)"
BD_PARENT_PROJECT="MD Cloud Menlo Container"
echo "Attempting to scan image $DOCKER_IMAGE"

cd ./kubernetes
./deploy.aws.sh ecr_login
cd ../
BD_PROJECT_VERSION=""
BD_VERSION_PHASE=""


echo "Project branching: develop (development) → main (deployment)"

# Determine version based on branch
if [[ "$BRANCH_NAME" == "develop" ]]; then
    BRANCH_TYPE="development"
elif [[ "$BRANCH_NAME" == "main" ]]; then
    BRANCH_TYPE="deployment"
else
    BRANCH_TYPE="other"
fi

# Determine Black Duck version based on branch type
case $BRANCH_TYPE in
    development)
        # Development branch → "main" version
        BD_PROJECT_VERSION="main"
        BLACKDUCK_VERSION_PHASE="DEVELOPMENT"
        echo "Detected development branch ($BRANCH_NAME) → version: main"
    ;;
    deployment)
        # Deployment branch with tag → use tag as version (e.g., v1.2.3)
        if [[ -n "$GIT_TAG" ]]; then
            BD_PROJECT_VERSION="${GIT_TAG}"
            BLACKDUCK_VERSION_PHASE="RELEASED"
            echo "Detected deployment branch ($BRANCH_NAME) with tag → version: $GIT_TAG"
        else
            BD_PROJECT_VERSION="deployment"
            BLACKDUCK_VERSION_PHASE="PRERELEASE"
            echo "Warning: deployment branch ($BRANCH_NAME) without tag → version: deployment"
        fi
    ;;
    other)
        # Check for feature/hotfix/release branches or default
        case $BRANCH_NAME in
            release/*|hotfix/*)
                # Release/hotfix branches → PRERELEASE
                BD_PROJECT_VERSION="${BRANCH_NAME}"
                BLACKDUCK_VERSION_PHASE="PRERELEASE"
                echo "Detected release/hotfix branch ($BRANCH_NAME) → version: $BRANCH_NAME (PRERELEASE)"
            ;;
            feature/*)
                # Feature branches → DEVELOPMENT
                BD_PROJECT_VERSION="${BRANCH_NAME}"
                BLACKDUCK_VERSION_PHASE="DEVELOPMENT"
                echo "Detected $BRANCH_NAME → version: $BRANCH_NAME"
            ;;
            *)
                # Default: use branch name
                BD_PROJECT_VERSION="${BRANCH_NAME}"
                BLACKDUCK_VERSION_PHASE="DEVELOPMENT"
                echo "Using branch name as version: $BRANCH_NAME"
            ;;
        esac
    ;;
esac

echo "Black Duck Version: $BD_PROJECT_VERSION"
echo "Black Duck Phase: $BLACKDUCK_VERSION_PHASE"

# Pull the Docker image
echo "Pulling Docker image from ECR..."
if ! docker pull "$DOCKER_IMAGE"; then
    echo "Failed to pull image: $DOCKER_IMAGE"
    exit 1
fi

IMAGE_TAR_FILE="/tmp/docker_image_$(date +%s).tar"

# Save Docker image
echo "Saving Docker image to $IMAGE_TAR_FILE..."
if ! docker save "$DOCKER_IMAGE" > "$IMAGE_TAR_FILE"; then
    echo "Failed to save image to tar file"
    exit 1
fi

# Verify the saved image
echo "Verifying saved image..."
if ! docker load < "$IMAGE_TAR_FILE" > /dev/null 2>&1; then
    echo "Error verifying saved image."
    rm -f "$IMAGE_TAR_FILE"
    exit 1
fi

# Download Synopsys Detect
echo "Downloading Synopsys Detect script..."
if ! curl -O https://detect.blackduck.com/detect10.sh; then
    echo "Failed to download Synopsys Detect script. Exiting."
    rm -f "$IMAGE_TAR_FILE"
    exit 1
fi
chmod +x detect10.sh
# Run Synopsys Detect
./detect10.sh \
    --blackduck.url="$BLACKDUCK_URL" \
    --blackduck.api.token="$BD_TOKEN" \
    --detect.project.name="$BD_PARENT_PROJECT" \
    --detect.project.version.name="$BD_PROJECT_VERSION" \
    --detect.project.version.phase="$BLACKDUCK_VERSION_PHASE" \
    --detect.container.scan.file.path="$IMAGE_TAR_FILE" \
    --detect.tools=CONTAINER_SCAN \
    --detect.tools.excluded=BINARY_SCAN \
    --detect.excluded.detector.types=pip \
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
else
    echo "Detect script succeeded for image: $DOCKER_IMAGE"
fi

# Cleanup
rm -f "$IMAGE_TAR_FILE"
echo "Scan complete."