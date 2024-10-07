#!/bin/bash

# Usage:
#
# export SONARQUBE_URL=?
# export SONARQUBE_TOKEN=?
# 
# ./tc-ci/sonarqube-scan.sh

CWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd );
cd $CWD/..
PWD=$( pwd )

PROJECT_VERSION=$(awk '/VERSION = / {print $3}' setup.py)

cat /etc/hosts | grep sonar.opswat.com
if [ $? != "0" ]; then
	echo "" >> /etc/hosts
	echo "10.192.9.121 sonar.opswat.com" >> /etc/hosts
fi

# TODO: Create a docker image with python 3.12
# install python 3.12
apt-get update && apt-get install -y \
    make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl \
    llvm libncurses5-dev libncursesw5-dev \
    xz-utils tk-dev libffi-dev liblzma-dev python-openssl \
    git

curl https://pyenv.run | bash

export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

pyenv install 3.12

# generate coverage report
make init && make coverage 

docker run \
    --rm \
    --network=host \
    -e SONAR_HOST_URL="${SONARQUBE_URL}" \
    -e SONAR_TOKEN="${SONARQUBE_TOKEN}" \
    -e SONAR_SCANNER_OPTS="-Dsonar.projectVersion=${PROJECT_VERSION}" \
    -v ${PWD}/:/usr/src \
    sonarsource/sonar-scanner-cli
