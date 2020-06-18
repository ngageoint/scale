#!/usr/bin/env bash

# Description: Creates all supported output document formats
# Usage: ./generate-outputs.sh
# Requires: Docker and perl installed locally
# Variables:
# ASCIDOCTOR_IMAGE: optional override for Asciidoctor Docker image
# PYTHON_IMAGE: optional override for Python 2.7.x Docker image
# SASS_IMAGE: optional override for Node SASS Docker image

: ${ASCIIDOCTOR_IMAGE:=rochdev/alpine-asciidoctor:mini}
: ${PYTHON_IMAGE:=python:2-alpine}
: ${SASS_IMAGE:=catchdigital/node-sass:8.12.0-alpine}

pushd $(dirname $0) > /dev/null

echo Generating HTML...
docker run -v $(pwd):/documents --rm ${ASCIIDOCTOR_IMAGE} asciidoctor -a stylesdir=./styles -a stylesheet=walkthrough.css -a imagesdir=../images -D /documents/output index.adoc

docker run -v $(pwd):/documents --rm ${ASCIIDOCTOR_IMAGE} sh generate-pdf.sh

popd > /dev/null
