#!/bin/bash

# Pulls docker images from a source environment, and pushes them to a destination environment.  

set -e # Exit on error

function check_required_vars() {
    local required_vars=(
        "AWS_REGION"
        "AWS_ACCOUNT_ID_SOURCE"
        "AWS_ACCOUNT_ID_DEST"
        "SOURCE_ENVIRONMENT"
        "DEST_ENVIRONMENT"
        "AWS_PROFILE_SOURCE"
        "AWS_PROFILE_DEST"
        "BUILD_VCS_NUMBER"
    )

    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -ne 0 ]; then
        echo "ERROR: Missing required environment variables:"
        printf '%s\n' "${missing_vars[@]}"
        exit 1
    fi
}

function change_used_account () {
    if [[ "$1" == "source" ]]; then 
        export AWS_ACCOUNT=${AWS_ACCOUNT_ID_SOURCE}
        export AWS_PROFILE=${AWS_PROFILE_SOURCE}
        export ENVIRONMENT=${SOURCE_ENVIRONMENT}
    else    
        export AWS_ACCOUNT=${AWS_ACCOUNT_ID_DEST}
        export AWS_PROFILE=${AWS_PROFILE_DEST}
        export ENVIRONMENT=${DEST_ENVIRONMENT}
    fi

    unset VERSION_PRUNED
    unset COMMIT_HASH 

    DOCKER_REPO="${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com"

    aws ecr get-login-password --profile ${AWS_PROFILE} --region "${AWS_REGION}" | docker login --username AWS --password-stdin ${DOCKER_REPO}

    echo "Changed to $1, account id : $AWS_ACCOUNT, repo : $DOCKER_REPO"
}

function generate_docker_image_name() {
    echo "${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/mdcl-menlo:${ENVIRONMENT}-m_${BUILD_VCS_NUMBER:0:7}"
}

# INFO : Main Start

check_required_vars

change_used_account "source"

DOCKER_IMAGE_SOURCE=$(generate_docker_image_name)

echo "Attempting to pull image $DOCKER_IMAGE_SOURCE"

docker pull $DOCKER_IMAGE_SOURCE

change_used_account "destination"

DOCKER_IMAGE_DEST=$(generate_docker_image_name)

docker tag $DOCKER_IMAGE_SOURCE $DOCKER_IMAGE_DEST

echo "Attempting to push image $DOCKER_IMAGE_DEST"

if [[ -z "${DRY_RUN}" ]]; then
    docker push $DOCKER_IMAGE_DEST
else
    echo "[DRY RUN] The following commands would be executed:"
    echo "  docker push ${DOCKER_IMAGE_DEST}" 
    echo "[DRY RUN] No changes were made"
fi