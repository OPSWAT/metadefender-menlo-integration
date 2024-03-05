#!/bin/bash

# Usage:
#
# export SONARQUBE_URL=?
# export SONARQUBE_TOKEN=?
# 
# ./tc-ci/sonarqube-scan.sh

# get current and project dir
CWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd ); cd $CWD/..; PWD=`pwd`

PROJECT_VERSION=$(awk '/VERSION = / {print $3}' setup.py)

cat /etc/hosts | grep sonar.opswat.com
if [ $? != "0" ]; then
	echo "" >> /etc/hosts
	echo "10.192.9.121 sonar.opswat.com" >> /etc/hosts
fi

docker run \
    --rm \
    --network=host \
    -e SONAR_HOST_URL="${SONARQUBE_URL}" \
    -e SONAR_TOKEN="${SONARQUBE_TOKEN}" \
    -e SONAR_SCANNER_OPTS="-Dsonar.projectVersion=${PROJECT_VERSION}" \
    -v ${PWD}/:/usr/src \
    sonarsource/sonar-scanner-cli
