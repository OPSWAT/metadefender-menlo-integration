#!/bin/bash

CWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd );
cd $CWD/..

export VERSION=m_"$(git rev-parse --short HEAD)"
DOCKER_IMAGE=${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/mdcl-menlo:${ENVIRONMENT}-$VERSION
BRANCH="$(git branch --show-current)"

echo "Attempting to scan image $DOCKER_IMAGE"

cd ./kubernetes

./deploy.aws.sh ecr_login

cd ../

case $BRANCH in
    customer)
        # customer branch / tag
        DETECT_PROJECT_VERSION_NAME="${BD_PARENT_PROJECT}-${VERSION}"
        BD_VERSION_PHASE="RELEASED"
    ;;
    release*)
        # release branch
        DETECT_PROJECT_VERSION_NAME="Release-HEAD"
        BD_VERSION_PHASE="PRERELEASE"
    ;;
    master|main|develop)
        # master branch
        DETECT_PROJECT_VERSION_NAME="main"
        BD_VERSION_PHASE="DEVELOPMENT"
    ;;
esac

bash <(curl -s -L https://detect.blackduck.com/detect9.sh) \
	--blackduck.api.token=\"${BD_TOKEN}\" \
	--blackduck.url=https://opswat.blackducksoftware.com  \
	--detect.docker.image="${DOCKER_IMAGE}" \
	--detect.project.name=\"MD Cloud Menlo\" \
	--detect.project.version.name="${DETECT_PROJECT_VERSION_NAME}" \
	--detect.project.version.phase="${BD_VERSION_PHASE}" \
	--detect.tools.excluded=BINARY_SCAN,SIGNATURE_SCAN \
  	--detect.excluded.detector.types=pip \
	--logging.level.com.synopsys.integration=DEBUG