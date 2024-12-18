#!/bin/bash

CWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd );
cd $CWD/..
BRANCH="$(git branch --show-current)"
PLUGIN_VERSION=$(awk '/VERSION = / {print $3}' setup.py)
BD_PARENT_PROJECT="MD Cloud Menlo"
python3 -m pip install --upgrade pip
pip install -r requirements.txt
echo "BRANCH: ${BRANCH}"
BD_PROJECT_VERSION=""
BD_VERSION_PHASE=""
case $BRANCH in
    customer)
        # customer branch / tag
        BD_PROJECT_VERSION=$BD_PARENT_PROJECT-$VERSION
        BD_VERSION_PHASE="RELEASED"
    ;;
    release*)
        # release branch
        BD_PROJECT_VERSION=$BD_PARENT_PROJECT-Release-HEAD
        BD_VERSION_PHASE="PRERELEASE"
    ;;
    master)
        # master branch
        BD_PROJECT_VERSION=$BD_PARENT_PROJECT-Develop-HEAD
        BD_VERSION_PHASE="DEVELOPMENT"
    ;;
    *)
        #other branches
        BD_PROJECT_VERSION=$BD_PARENT_PROJECT-$BRANCH_NAME
        BD_VERSION_PHASE="DEVELOPMENT"
    ;;
esac;
echo "DETECT_PROJECT_VERSION_NAME: ${BD_PROJECT_VERSION}"


bash <(curl -s -L https://detect.synopsys.com/detect9.sh) --detect.timeout=3600\
    --blackduck.api.token=\"${BD_TOKEN}\" \
    --blackduck.url=https://opswat.blackducksoftware.com  \
    --detect.blackduck.signature.scanner.upload.source.mode=false \
    --detect.detector.search.exclusion.paths=docker \
    --detect.notices.report=true \
    --detect.pip.requirements.path=requirements.txt \
    --detect.policy.check.fail.on.severities=BLOCKER,CRITICAL \
    --detect.project.name="${BD_PARENT_PROJECT}" \
    --detect.project.version.name="${BD_PROJECT_VERSION}" \
    --detect.project.version.phase="${BD_VERSION_PHASE}" \
    --detect.python.path=/usr/bin/python3 \
    --detect.tools.excluded=SIGNATURE_SCAN \
    --logging.level.com.synopsys.integration=DEBUG