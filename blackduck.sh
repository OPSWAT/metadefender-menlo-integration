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
    --blackduck.api.token=$1 \
    --blackduck.trust.cert=true \
    --blackduck.url=https://opswat.blackducksoftware.com \
    --detect.blackduck.signature.scanner.upload.source.mode=false \
    --detect.detector.search.exclusion.paths=docker \
    --detect.pip.requirements.path=requirements.txt \
    --detect.project.name=\"MD Cloud Menlo\" \
    --detect.project.version.name=menlo-plugin-$PLUGIN_VERSION \
    --detect.python.python3=true \
    --detect.tools.excluded=SIGNATURE_SCAN \
    --logging.level.com.synopsys.integration=DEBUG
