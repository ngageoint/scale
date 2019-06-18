#!/usr/bin/env sh
set -e

BASE_IMAGE=$1
COMPONENT=$2

if [[ "${CI_BUILD_TAG}x" == "x" ]]
then
    docker login -u ${DOCKER_DEV_USER} -p "${DOCKER_DEV_PASS}" ${REGISTRY}

    export IMAGE_URL=${REGISTRY}/${DOCKER_DEV_ORG}/${IMAGE_PREFIX}-${COMPONENT}
    docker pull ${IMAGE_URL} || true

    docker build \
        -t ${IMAGE_URL}:${CI_BUILD_TAG} \
        --label VERSION=${CI_BUILD_TAG} \
        --build-arg VAULT_ZIP=${VAULT_ZIP} \
        --build-arg IMAGE=${BASE_IMAGE} \
        dockerfiles/${COMPONENT}

    docker push ${IMAGE_URL}
    docker push ${IMAGE_URL}:${CI_BUILD_TAG}
else
    docker login -u ${DOCKER_USER} -p "${DOCKER_PASS}" ${REGISTRY}

    export IMAGE_URL=${REGISTRY}/${DOCKER_ORG}/${IMAGE_PREFIX}
    docker pull ${IMAGE_URL} || true

    docker build \
        -t ${IMAGE_URL}:${CI_BUILD_TAG} \
        --label VERSION=${CI_BUILD_TAG} \
        --build-arg VAULT_ZIP=${VAULT_ZIP} \
        --build-arg IMAGE=${BASE_IMAGE} \
        dockerfiles/${COMPONENT}

    docker push ${IMAGE_URL}
    docker push ${IMAGE_URL}:${CI_BUILD_TAG}
fi
