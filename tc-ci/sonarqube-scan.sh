#!/bin/bash
#############################
# Runs SonarQube code analysis using sonar-scanner-cli Docker container.
# Scans source code and uploads results to SonarQube server.
#
# Used in: <TeamCity: ... > ... >
#
# Parameters:
# None - uses TeamCity parameters
#
# Environment Variables:
# SONARQUBE_URL   - SonarQube server URL
# SONARQUBE_TOKEN - Authentication token for SonarQube
# %teamcity.build.branch% - Branch name from TeamCity
#############################
set -e

PROJECT_VERSION=$(awk '/VERSION = / {print $3}' setup.py)

cat /etc/hosts | grep sonar.opswat.com
if [ $? != "0" ]; then
	echo "" >> /etc/hosts
	echo "10.192.9.121 sonar.opswat.com" >> /etc/hosts
fi

BRANCH_NAME="%teamcity.build.branch%"

docker run \
    --rm \
    --network=host \
    -e SONAR_HOST_URL="${SONARQUBE_URL}" \
    -e SONAR_TOKEN="${SONARQUBE_TOKEN}" \
    -e SONAR_SCANNER_OPTS="-Dsonar.projectVersion=${PROJECT_VERSION}  -Dsonar.ws.timeout=300" \
    -v ${PWD}/:/usr/src \
    sonarsource/sonar-scanner-cli \
    -Dsonar.branch.name="${BRANCH_NAME}"