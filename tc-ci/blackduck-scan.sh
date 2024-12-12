#!/bin/bash

CWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd );
cd $CWD/..
BRANCH="$(git branch --show-current)"
PLUGIN_VERSION=$(awk '/VERSION = / {print $3}' setup.py)

python3 -m pip install --upgrade pip
pip install -r requirements.txt
echo "${BRANCH}"
if [[ "$BRANCH" == "master" || "$BRANCH" == "main" ]]; then
    DETECT_PROJECT_VERSION_NAME="main"
elif [[ "$BRANCH" == "release" ]]; then
    DETECT_PROJECT_VERSION_NAME="Release-HEAD"
else
    DETECT_PROJECT_VERSION_NAME="MD Cloud Menlo-${PLUGIN_VERSION}"
fi
echo "${DETECT_PROJECT_VERSION_NAME}"


bash <(curl -s -L https://detect.synopsys.com/detect9.sh) --detect.timeout=3600\
    --blackduck.api.token=\"${BD_TOKEN}\" \
    --blackduck.url=https://opswat.blackducksoftware.com  \
    --detect.blackduck.signature.scanner.upload.source.mode=false \
    --detect.detector.search.exclusion.paths=docker \
    --detect.notices.report=true \
    --detect.pip.requirements.path=requirements.txt \
    --detect.policy.check.fail.on.severities=BLOCKER,CRITICAL \
    --detect.project.name="MD Cloud Menlo" \
    --detect.project.version.name="${DETECT_PROJECT_VERSION_NAME}" \
    --detect.project.version.phase="${BD_VERSION_PHASE}" \
    --detect.python.path=/usr/bin/python3 \
    --detect.tools.excluded=SIGNATURE_SCAN \
    --logging.level.com.synopsys.integration=DEBUG