#!/bin/bash

# Usage:
# 
# export AWS_ACCOUNT=?
# export AWS_REGION=?
# export VERSION=?
# export ENVIRONMENT=?
# export BD_TOKEN=?
# export BD_VERSION_PHASE=?
# ./blackduck-scan.sh

DOCKER_IMAGE=${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/mdcl-menlo:${ENVIRONMENT}-$VERSION
echo "Attempting to scan image $DOCKER_IMAGE"

./kubernetes/deploy.aws.sh ecr_login


PLUGIN_VERSION=$(awk '/VERSION = / {print $3}' setup.py)

bash blackduck.detect.sh \
	--blackduck.api.token=\"${BD_TOKEN}\" \
	--blackduck.trust.cert=true \
	--blackduck.url=https://opswat.blackducksoftware.com  \
	--detect.docker.image="${IMAGE}" \
	--detect.project.name=\"MD Cloud Menlo\" \
	--detect.project.version.name=menlo-plugin-$PLUGIN_VERSION-container \
	--detect.project.version.phase=\"${BD_VERSION_PHASE}\" \
	--detect.tools.excluded=BINARY_SCAN,SIGNATURE_SCAN \
  	--detect.excluded.detector.types=pip \
	--logging.level.com.synopsys.integration=DEBUG
  # --detect.output.path="$BITBUCKET_CLONE_DIR/blackduck" \