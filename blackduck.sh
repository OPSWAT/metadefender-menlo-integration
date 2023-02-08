#!/bin/bash
# Usage:
# ./blackduck.sh <token> [<dev-version>]
# <token>       - blackducl token
# <dev-version> - set to any non-empty value to specify that this is a development version

if [[ $1 == '' ]]; then
    echo "Missing blackduck token."
    echo "Usage:"
    echo "./blackduck.sh <token> [<dev-version>]"
    exit 1
fi

PLUGIN_VERSION=$(awk '/VERSION = / {print $3}' setup.py)

if [[ $2 != '' ]]; then
    PLUGIN_VERSION=${PLUGIN_VERSION}-rc
fi

if [[ $BITBUCKET_PIPELINE_UUID != '' ]]; then
    # script runs as Bitbucket pipeline
    apk add --no-cache openjdk11 curl bash
    BDS_JAVA_HOME=/usr/lib/jvm/default-jvm/jre
fi

export DETECT_LATEST_RELEASE_VERSION=6.9.1
export DETECT_VERSION_KEY=DETECT_LATEST_6
bash blackduck.detect.sh \
    --logging.level.com.synopsys.integration=DEBUG \
    --detect.python.python3=true \
    --detect.blackduck.signature.scanner.upload.source.mode=false \
    --detect.pip.requirements.path=requirements.txt \
    --blackduck.api.token=$1 \
    --blackduck.url=https://opswat.blackducksoftware.com \
    --blackduck.trust.cert=true \
    --detect.project.name=\"MD Cloud Menlo\" \
    --detect.project.version.name=menlo-plugin-$PLUGIN_VERSION \
    --detect.detector.search.exclusion.paths=docker \
    --detect.tools.excluded=SIGNATURE_SCAN
