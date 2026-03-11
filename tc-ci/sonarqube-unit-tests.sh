#!/bin/bash
#############################
# Runs unit tests with coverage report for SonarQube analysis.
# Generates coverage.xml in tests/coverage/ directory.
#
# Used in: <TeamCity: ... > ... >
#
# Parameters:
# None
#
# Requirements:
# - Python 3.11 container or environment
# - menlo.sh script with 'coverage' command
#############################
set -e

ls -al
pwd

if ! command -v python3 &> /dev/null; then
    if command -v python3.11 &> /dev/null; then
        mkdir -p "$HOME/bin"
        ln -sf "$(command -v python3.11)" "$HOME/bin/python3"
        export PATH="$HOME/bin:$PATH"
    else
        echo "ERROR: python3 is not installed or not in PATH" >&2
        exit 1
    fi
fi
python3 --version

PROJECT_VERSION=$(awk '/VERSION = / {print $3}' setup.py)

mkdir -p tests/coverage
chmod +x menlo.sh
./menlo.sh coverage

file tests/coverage/coverage.xml
head -20 tests/coverage/coverage.xml