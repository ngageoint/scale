#!/usr/bin/env sh
set -e

BASE_IMAGE=$1
COMPONENT=$2

docker login -u ${DOCKER_USER} -p "${DOCKER_PASS}" ${REGISTRY}

IMAGE_URL=${REGISTRY}/${DOCKER_ORG}/${IMAGE_PREFIX}-${COMPONENT}
docker pull ${IMAGE_URL} || true

docker build \
    -t ${IMAGE_URL}:${CI_BUILD_TAG} \
    --build-arg VAULT_ZIP=${VAULT_ZIP} \
    --build-arg IMAGE=${BASE_IMAGE} \
    dockerfiles/${COMPONENT}
docker push ${IMAGE_URL}:${CI_BUILD_TAG}

