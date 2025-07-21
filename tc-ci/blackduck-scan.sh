#!/bin/bash

BRANCH="$(git branch --show-current)"
TAG="$(git describe --tags --exact-match 2>/dev/null)"
PLUGIN_VERSION=$(awk '/VERSION = / {print $3}' setup.py)
BD_PARENT_PROJECT="MD Cloud Menlo"
VERSION=${PLUGIN_VERSION:-"unknown"}  # Use PLUGIN_VERSION or fallback to "unknown"

python3 -m pip install --upgrade pip
pip install -r requirements.txt

BD_PROJECT_VERSION=""
BD_VERSION_PHASE=""

if [[ -n "$TAG" ]]; then
    BD_PROJECT_VERSION="${BD_PARENT_PROJECT}-${TAG}"
    BD_VERSION_PHASE="RELEASED"
else
    if [[ $BRANCH =~ ^[[:digit:]] ]]; then
        VERSION=$BRANCH
        BRANCH="customer"
    fi

    if [[ $BRANCH =~ ^release/[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        VERSION=$(echo "$BRANCH" | sed -E 's|^release/([0-9]+\.[0-9]+\.[0-9]+)$|\1|')
        BRANCH="release"
    fi
    
    case $BRANCH in
        customer)
            BD_PROJECT_VERSION="Customer-${VERSION}"
            BD_VERSION_PHASE="RELEASED"
        ;;
        release)
            BD_PROJECT_VERSION="Pre-Release-${VERSION}"
            BD_VERSION_PHASE="PRERELEASE"
        ;;
        master|main|develop)
            BD_PROJECT_VERSION="main"
            BD_VERSION_PHASE="DEVELOPMENT"
        ;;
        feature*)
            BD_PROJECT_VERSION="${BRANCH}"
            BD_VERSION_PHASE="DEVELOPMENT"
        ;;
    esac
fi

echo "DEBUG VARS: "
echo "BRANCH: ${BRANCH}"
echo "BD_PROJECT_VERSION: ${BD_PROJECT_VERSION}"
echo "BD_VERSION_PHASE: ${BD_VERSION_PHASE}"

echo "##teamcity[blockOpened name='BlackDuck Container Scan']"

bash <(curl -s -L https://detect.blackduck.com/detect9.sh) --detect.timeout=3600 \
    --blackduck.api.token="${BD_TOKEN}" \
    --blackduck.url=https://opswat.blackducksoftware.com  \
    --detect.blackduck.signature.scanner.upload.source.mode=false \
    --detect.detector.search.exclusion.paths=docker \
    --detect.notices.report=true \
    --detect.pip.requirements.path=requirements.txt \
    --detect.policy.check.fail.on.severities=BLOCKER,CRITICAL \
    --detect.project.name="${BD_PARENT_PROJECT}" \
    --detect.project.version.name="${BD_PROJECT_VERSION}" \
    --detect.project.version.phase="${BD_VERSION_PHASE}" \
    --detect.python.path=/usr/bin/python3 \
    --detect.tools.excluded=SIGNATURE_SCAN \
    --logging.level.com.synopsys.integration=DEBUG

echo "##teamcity[blockClosed name='BlackDuck Container Scan']"