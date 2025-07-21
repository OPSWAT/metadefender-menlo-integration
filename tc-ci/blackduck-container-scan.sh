#!/bin/bash

CWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd );
cd $CWD/..

export VERSION=m_"$(git rev-parse --short HEAD)"
DOCKER_IMAGE=${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/opswat/mdcl-menlo:${ENVIRONMENT}-$VERSION
BRANCH="$(git branch --show-current)"
TAG="$(git describe --tags --exact-match 2>/dev/null)"
BD_PARENT_PROJECT="MD Cloud Menlo"
echo "Attempting to scan image $DOCKER_IMAGE"

cd ./kubernetes

./deploy.aws.sh ecr_login

cd ../
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
echo "##teamcity[blockOpened name='BlackDuck Container Scan']"

bash <(curl -s -L https://detect.blackduck.com/detect9.sh) \
	--blackduck.api.token=\"${BD_TOKEN}\" \
	--blackduck.url=https://opswat.blackducksoftware.com  \
	--detect.docker.image="${DOCKER_IMAGE}" \
	--detect.project.name="${BD_PARENT_PROJECT}" \
	--detect.project.version.name="${BD_PROJECT_VERSION}" \
	--detect.project.version.phase="${BD_VERSION_PHASE}" \
	--detect.tools.excluded=BINARY_SCAN,SIGNATURE_SCAN \
  	--detect.excluded.detector.types=pip \
	--logging.level.com.synopsys.integration=DEBUG

echo "##teamcity[blockClosed name='BlackDuck Container Scan']"