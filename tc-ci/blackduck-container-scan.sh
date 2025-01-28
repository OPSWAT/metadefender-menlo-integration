#!/bin/bash

CWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd );
cd $CWD/..

export VERSION=m_"$(git rev-parse --short HEAD)"
DOCKER_IMAGE=${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/mdcl-menlo:${ENVIRONMENT}-$VERSION
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
    # tag
    BD_PROJECT_VERSION="${BD_PARENT_PROJECT}-${TAG}"
    BD_VERSION_PHASE="RELEASED"
else
    case $BRANCH in
        customer)
            # customer branch
            BD_PROJECT_VERSION="${BD_PARENT_PROJECT}-${VERSION}"
            BD_VERSION_PHASE="RELEASED"
        ;;
        release*)
            # release branch
            BD_PROJECT_VERSION="Release-HEAD"
            BD_VERSION_PHASE="PRERELEASE"
        ;;
        master|main|develop)
            # master branch
            BD_PROJECT_VERSION="main"
            BD_VERSION_PHASE="DEVELOPMENT"
        ;;
    esac
fi

bash <(curl -s -L https://detect.synopsys.com/detect9.sh) \
	--blackduck.api.token=\"${BD_TOKEN}\" \
	--blackduck.url=https://opswat.blackducksoftware.com  \
	--detect.docker.image="${DOCKER_IMAGE}" \
	--detect.project.name="${BD_PARENT_PROJECT}" \
	--detect.project.version.name="${BD_PROJECT_VERSION}" \
	--detect.project.version.phase="${BD_VERSION_PHASE}" \
	--detect.tools.excluded=BINARY_SCAN,SIGNATURE_SCAN \
  	--detect.excluded.detector.types=pip \
	--logging.level.com.synopsys.integration=DEBUG