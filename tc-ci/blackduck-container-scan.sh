#!/bin/bash

# Usage:
# 
# export AWS_ACCOUNT=?
# export AWS_REGION=?
# export ENVIRONMENT=?
# export BD_TOKEN=?
# export BD_VERSION_PHASE=?
#
# ./tc-ci/blackduck-scan.sh

CWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd );
cd $CWD/..

export VERSION=m_`git rev-parse --short HEAD`
DOCKER_IMAGE=${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/mdcl-menlo:${ENVIRONMENT}-$VERSION
PLUGIN_VERSION=$(awk '/VERSION = / {print $3}' setup.py)

echo "Attempting to scan image $DOCKER_IMAGE"

cd ./kubernetes

./deploy.aws.sh ecr_login

cd ../

bash <(curl -s -L https://detect.synopsys.com/detect9.sh) \
	--blackduck.api.token=\"${BD_TOKEN}\" \
	--blackduck.url=https://opswat.blackducksoftware.com  \
	--detect.docker.image="${DOCKER_IMAGE}" \
	--detect.project.name=\"MD Cloud Menlo\" \
	--detect.project.version.name=menlo-plugin-$PLUGIN_VERSION-container \
	--detect.project.version.phase=\"${BD_VERSION_PHASE}\" \
	--detect.tools.excluded=BINARY_SCAN,SIGNATURE_SCAN \
  	--detect.excluded.detector.types=pip \
	--logging.level.com.synopsys.integration=DEBUG