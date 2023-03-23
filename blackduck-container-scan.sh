#!/bin/bash

while [[ $# -gt 0 ]]; do
  case "${1}" in
    -t|--token)
      shift
      BLACKDUCK_TOKEN=${1}
      shift
      ;;
    -i|--image)
      shift
      IMAGE=${1}
      shift
      ;;
     *)
      shift
      echo "Unsupported parameter"
      echo "Supported parameters are: -t --token -i --image"
      exit 1
      ;;
  esac
done

apk add --no-cache openjdk11 curl bash
BDS_JAVA_HOME=/usr/lib/jvm/default-jvm/jre

MENLO_VERSION=$(awk '/VERSION = / {print $3}' setup.py)

echo "Login to AWS ECR" 
$(aws ecr get-login --no-include-email --region us-west-2)
if [[ "$?" != "0" ]]; then
    exit 1
fi

bash <(curl -s -L https://detect.synopsys.com/detect8.sh) \
	--blackduck.url=https://opswat.blackducksoftware.com  \
	--blackduck.api.token=\"${BLACKDUCK_TOKEN}\" \
	--blackduck.trust.cert=true \
	--detect.docker.image="${IMAGE}" \
	--detect.project.name=\"MD Cloud Menlo\" \
	--detect.project.version.name=menlo-plugin-$MENLO_VERSION-container \
	--detect.project.version.phase=DEVELOPMENT \
	--detect.tools.excluded=BINARY_SCAN \
	--logging.level.com.synopsys.integration=DEBUG