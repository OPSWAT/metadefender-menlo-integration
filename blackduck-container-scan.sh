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

export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID_dev
export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY_dev
export AWS_REGION=us-west-2
export AWS_ACCOUNT=108895011981
echo "Login to AWS ECR"
./kubernetes/deploy.aws.sh ecr_login

apk add --no-cache openjdk11 curl bash
BDS_JAVA_HOME=/usr/lib/jvm/default-jvm/jre

MENLO_VERSION=$(awk '/VERSION = / {print $3}' setup.py)
which pip

bash <(curl -s -L https://detect.synopsys.com/detect8.sh) \
	--blackduck.url=https://opswat.blackducksoftware.com  \
	--blackduck.api.token=\"${BLACKDUCK_TOKEN}\" \
	--blackduck.trust.cert=true \
	--detect.docker.image="${IMAGE}" \
	--detect.project.name=\"MD Cloud Menlo\" \
	--detect.project.version.name=menlo-plugin-$MENLO_VERSION-container \
	--detect.project.version.phase=DEVELOPMENT \
	--detect.tools.excluded=BINARY_SCAN,SIGNATURE_SCAN \
  --detect.output.path="$BITBUCKET_CLONE_DIR/blackduck" \
  --detect.python.path="/usr/bin/pip" \
  --detect.pip.requirements.path=requirements.txt \
	--logging.level.com.synopsys.integration=DEBUG