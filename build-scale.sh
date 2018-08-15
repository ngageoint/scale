#!/usr/bin/env sh
set -e

# When CI_BUILD_TAG is unset we are building a snapshot
if [[ "${CI_BUILD_TAG}x" == "x" ]]
then
    docker login -u ${DOCKER_DEV_USER} -p ${DOCKER_DEV_PASS} ${REGISTRY}

    export IMAGE_URL=${REGISTRY}/${DOCKER_DEV_ORG}/${IMAGE_PREFIX}

    # Grab latest for caching purposes
    docker pull ${IMAGE_URL} || true
    docker build \
        --cache-from ${IMAGE_URL} \
        --build-arg EPEL_INSTALL=${EPEL_INSTALL} \
        --build-arg IMAGE=${CENTOS_IMAGE} \
        --build-arg BUILDNUM=${CI_BUILD_REF:0:8} \
        --build-arg GOSU_URL=${GOSU_URL} \
        -t ${IMAGE_URL} .

    export SCALE_VERSION=$(docker run --entrypoint /bin/bash ${IMAGE_URL} -c 'python -c "import scale; print(scale.__docker_version__)"')
    docker tag ${IMAGE_URL} ${IMAGE_URL}:${SCALE_VERSION}

    docker push ${IMAGE_URL}
    docker push ${IMAGE_URL}:${SCALE_VERSION}
else
    docker login -u ${DOCKER_USER} -p ${DOCKER_PASS} ${REGISTRY}

    export IMAGE_URL=${REGISTRY}/${DOCKER_ORG}/${IMAGE_PREFIX}

    # Grab latest for caching purposes
    docker pull ${IMAGE_URL} || true

    docker build \
        --build-arg EPEL_INSTALL=${EPEL_INSTALL} \
        --build-arg IMAGE=${CENTOS_IMAGE} \
        --build-arg GOSU_URL=${GOSU_URL} \
        -t ${IMAGE_URL} \
        -t ${IMAGE_URL}:${CI_BUILD_TAG} .

    docker push ${IMAGE_URL}
    docker push ${IMAGE_URL}:${CI_BUILD_TAG}
fi

