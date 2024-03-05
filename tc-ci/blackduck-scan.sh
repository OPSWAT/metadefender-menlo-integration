#!/bin/bash

# Usage:
# 
# export BD_TOKEN=?
# export BD_VERSION_PHASE=?
#
# ./tc-ci/blackduck-scan.sh

CWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd );
cd $CWD/..

PLUGIN_VERSION=$(awk '/VERSION = / {print $3}' setup.py)

bash blackduck.detect.sh \
    --blackduck.api.token=\"${BD_TOKEN}\" \
    --blackduck.trust.cert=true \
    --blackduck.url=https://opswat.blackducksoftware.com  \
    --detect.blackduck.signature.scanner.upload.source.mode=false \
    --detect.detector.search.exclusion.paths=docker \
    --detect.notices.report=true \
    --detect.npm.arguments=\"--depth=0 --silent\" \
    --detect.pip.requirements.path=requirements.txt \
    --detect.policy.check.fail.on.severities=BLOCKER,CRITICAL \
    --detect.project.name=\"MD Cloud Menlo\" \
    --detect.project.version.name=menlo-plugin-$PLUGIN_VERSION \
    --detect.project.version.phase=\"${BD_VERSION_PHASE}\" \
    --detect.python.path=/usr/bin/python3 \
    --detect.tools.excluded=SIGNATURE_SCAN \
    --logging.level.com.synopsys.integration=DEBUG