#!/usr/bin/env sh
set -e

# When CI_BUILD_TAG is unset we are building a snapshot
if [[ "${CI_BUILD_TAG}x" == "x" ]]
then
    export DOCKER_USER=${DOCKER_DEV_USER}
    export DOCKER_AUTH_CONFIG=${DOCKER_DEV_AUTH_CONFIG}
    # This must be provided in docker dind image as a means to inject login configs from DOCKER_AUTH_CONFIG env
    # We only use this as we are not using the default user for snapshot builds
    inject-auth-env.sh

    export IMAGE_URL=${REGISTRY}/${DOCKER_USER}/${IMAGE_PREFIX}
    docker build --build-arg EPEL_INSTALL=${EPEL_INSTALL} --build-arg IMAGE=${CENTOS_IMAGE} --build-arg BUILDNUM=${CI_BUILD_REF:0:8} --build-arg GOSU_URL=${GOSU_URL} -t ${IMAGE_URL} .

    export SCALE_VERSION=$(docker run --entrypoint /bin/bash ${IMAGE_URL} -c 'python -c "import scale; print(scale.__docker_version__)"')
    docker tag ${IMAGE_URL} ${IMAGE_URL}:${SCALE_VERSION}

    docker push ${IMAGE_URL}:${SCALE_VERSION}
else
    export IMAGE_URL=${REGISTRY}/${DOCKER_USER}/${IMAGE_PREFIX}:${CI_BUILD_TAG}
    docker build --build-arg EPEL_INSTALL=${EPEL_INSTALL} --build-arg IMAGE=${CENTOS_IMAGE} --build-arg GOSU_URL=${GOSU_URL} -t ${IMAGE_URL} .

    docker push ${IMAGE_URL}
fi

