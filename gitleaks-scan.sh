#!/bin/bash

# Usage:
#
# ./gitleaks-scan.sh

docker run -v ${PWD}:/project zricethezav/gitleaks:latest detect -s /project -v --no-git --redact -r /project/gitleaks.json
