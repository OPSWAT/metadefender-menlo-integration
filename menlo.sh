#!/usr/bin/env bash

HELP_MENLO="
    setup                   # setup environment
    help                    # show this message
    unit                    # run unit tests
    integration             # run integration tests
"

function printHelp {
    echo -e "${HELP_MENLO}"
}

function setup {
    echo "Setting up environment..."
    
    which python3 &> /dev/null || (echo "Python3 is not installed" && exit 1)
    python3 --version
    
    if [ ! -d .venv ]; then
        echo "Creating virtual environment..." 
        python3 -m venv .venv
    fi

    source .venv/bin/activate

    echo "Installing dependencies..."
    pip install -r requirements.txt
}

if [[ $# == 0 ]]; then
    printHelp
    exit 0
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help|help)
            printHelp
            exit 0
            ;;
        setup)
            setup
            ;;
        unit)
            echo "Running unit tests..."
            python3 -m unittest discover -v ./tests/unit -p 'test*.py'
            ;;
        integration)
            echo "Running integration tests..."
            python3 -m unittest discover -v ./tests/integration -p 'tests*.py'
            ;;
        coverage)
            echo "Running coverage..."
            ./.venv/bin/python3 -m pytest --cov=. --cov-report=xml:reports/coverage.xml
            ;;
        *)
            echo "Unknown parameter: ${1}"
            printHelp
            exit 1
    esac

    shift
done 