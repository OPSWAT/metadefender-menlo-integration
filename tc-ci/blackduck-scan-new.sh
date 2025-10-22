#!/bin/bash

# Set Black Duck variables from TeamCity environment or parameters
BD_PARENT_PROJECT="${black_duck_parent_project}"
BD_TOKEN="${black_duck_token}"
BLACKDUCK_URL="https://opswat.blackducksoftware.com/"

# Get branch name (handle detached HEAD)
BRANCH_NAME="${BRANCH_NAME:-$(git branch --show-current 2>/dev/null)}"
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

echo "Branch/Tag: $BRANCH_NAME"
BD_PROJECT_VERSION=""
BLACKDUCK_VERSION_PHASE=""

case "$BRANCH_NAME" in
    *develop*|*master*)
        BD_PROJECT_VERSION="main"
        BLACKDUCK_VERSION_PHASE="DEVELOPMENT"
        echo "Detected main branch ($BRANCH_NAME) → version: main"
        ;;
    main|customer)
        BD_PROJECT_VERSION="customer"
        BLACKDUCK_VERSION_PHASE="RELEASED"
        echo "Detected customer branch → version: ${BRANCH_NAME}"
        ;;
    release/*|hotfix/*)
        BD_PROJECT_VERSION="${BRANCH_NAME}"
        BLACKDUCK_VERSION_PHASE="PRERELEASE"
        echo "Detected release/hotfix branch → version: ${BRANCH_NAME} (PRERELEASE)"
        ;;
    feature/*)
        BD_PROJECT_VERSION="${BRANCH_NAME}"
        BLACKDUCK_VERSION_PHASE="DEVELOPMENT"
        echo "Detected feature branch → version: ${BRANCH_NAME}"
        ;;
    [0-9]*)
        # Version tag (e.g., 1.2.3)
        BD_PROJECT_VERSION="v${BRANCH_NAME}"
        BLACKDUCK_VERSION_PHASE="RELEASED"
        echo "Detected version tag ($BRANCH_NAME) → version: v${BRANCH_NAME}"
        ;;
    *)
        BD_PROJECT_VERSION="${BRANCH_NAME}"
        BLACKDUCK_VERSION_PHASE="DEVELOPMENT"
        echo "Using branch name as version: ${BRANCH_NAME}"
        ;;
esac

echo "Black Duck Project: $BD_PARENT_PROJECT"
echo "Black Duck Version: $BD_PROJECT_VERSION"
echo "Black Duck Phase: $BLACKDUCK_VERSION_PHASE"

# Install Python dependencies
echo "##teamcity[blockOpened name='Install Dependencies']"
echo "Installing Python dependencies..."
python3 -m pip install --upgrade pip
pip install -r requirements.txt
echo "##teamcity[blockClosed name='Install Dependencies']"

echo "##teamcity[blockOpened name='Download Detect Script']"
echo "Downloading Synopsys Detect script..."
if ! curl -O https://detect.blackduck.com/detect10.sh; then
    echo "Failed to download Synopsys Detect script. Exiting."
    echo "##teamcity[blockClosed name='Download Detect Script']"
    exit 1
fi
chmod +x detect10.sh
echo "##teamcity[blockClosed name='Download Detect Script']"

echo "##teamcity[blockOpened name='BlackDuck Detect Scan - $BD_PROJECT_VERSION']"

# Set excluded directories for Menlo middleware project
EXCLUDED_DIRS="docker,kubernetes,tc-ci,docs,api,__pycache__,.git,logs,tmp,temp,coverage"
echo "Menlo middleware project: using project-specific exclusions: $EXCLUDED_DIRS"

./detect10.sh \
    --blackduck.url="$BLACKDUCK_URL" \
    --blackduck.api.token="$BD_TOKEN" \
    --detect.project.name="$BD_PARENT_PROJECT" \
    --detect.project.version.name="$BD_PROJECT_VERSION" \
    --detect.project.version.phase="$BLACKDUCK_VERSION_PHASE" \
    --detect.project.version.distribution=SAAS \
    --detect.excluded.directories="$EXCLUDED_DIRS" \
    --detect.tools.excluded=SIGNATURE_SCAN \
    --detect.detector.search.depth=1 \
    --detect.notices.report=true \
    --detect.accuracy.required=NONE \
    --detect.pip.requirements.path=requirements.txt \
    --detect.python.path=/usr/bin/python3 \
    --detect.policy.check.fail.on.severities=BLOCKER,CRITICAL \
    --detect.timeout=3600 \
    --logging.level.com.synopsys.integration=DEBUG

detect_exit_code="$?"
if [[ "$detect_exit_code" != "0" ]]; then
    echo "Detect script failed with exit code: $detect_exit_code"
    echo "##teamcity[blockClosed name='BlackDuck Detect Scan - $BD_PROJECT_VERSION']"
    exit 1
fi

echo "##teamcity[blockClosed name='BlackDuck Detect Scan - $BD_PROJECT_VERSION']"
echo "Scan completed successfully for $BD_PROJECT_VERSION"
