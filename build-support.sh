#!/usr/bin/env sh
set -e

BASE_IMAGE=$1
COMPONENT=$2

IMAGE_URL=${REGISTRY}/${DOCKER_USER}/${IMAGE_PREFIX}-${COMPONENT}:${CI_BUILD_TAG}

docker build -t ${IMAGE_URL} --build-arg IMAGE=${BASE_IMAGE} dockerfiles/${COMPONENT}
docker push ${IMAGE_URL}

