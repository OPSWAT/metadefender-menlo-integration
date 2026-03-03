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

DOCKER_ADD_HOST=""
if ! grep -q "sonar.opswat.com" /etc/hosts; then
    DOCKER_ADD_HOST="--add-host=sonar.opswat.com:10.192.9.121"
fi

BRANCH_NAME="%teamcity.build.branch%"

docker run \
    --rm \
    --network=host \
    ${DOCKER_ADD_HOST} \
    -e SONAR_HOST_URL="${SONARQUBE_URL}" \
    -e SONAR_TOKEN="${SONARQUBE_TOKEN}" \
    -v ${PWD}/:/usr/src \
    sonarsource/sonar-scanner-cli \
    -Dsonar.branch.name="${BRANCH_NAME}"