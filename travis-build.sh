#!/usr/bin/env bash

set -e

root=$(dirname $0)
cd $root
root=`pwd`

if [ "${RUN_TESTS}" == "true" ]
then
    cd $root/scale
    cp scale/local_settings_TRAVIS-CI.py scale/local_settings.py
    psql -c 'create database scale;' -U postgres
    psql -d scale -U postgres -c "create extension postgis;"
    psql -d scale -U postgres -c "create extension postgis_topology;"

    export COVERAGE_FILE=$root/.coverage
    coverage run --source='.' manage.py test
fi

if [ "${BUILD_DOCS}" == "true" ]
then
    cd $root/scale/docs
    make code_docs html
    # Generate walkthrough HTML from AsciiDoc
    cd $root/web-docs/walkthrough
    ./generate-outputs.sh
    cd $root
    ./push-docs.sh
fi

cd $root
