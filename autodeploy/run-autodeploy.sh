#!/usr/bin/env sh

ARGS=$@
docker run --rm -v "${PWD}:/usr/autodeploy/volume" mtalda/autodeploy ${ARGS}
 