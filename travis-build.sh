#!/usr/bin/env bash

set -e

root=$(dirname $0)
cd $root
root=`pwd`

# DISABLED as no unit tests exist for UI. Add NodeJS 6 to build dependencies
#wget https://raw.githubusercontent.com/creationix/nvm/v0.31.0/nvm.sh -O ~/.nvm/nvm.sh
#source ~/.nvm/nvm.sh
#nvm install 6

cd $root/scale-ui
./travis-build.sh


if [ ${RUN_TESTS} == 'true' ]
then
    cd $root/scale
    cp scale/local_settings_TRAVIS-CI.py scale/local_settings.py
    psql -c 'create database scale;' -U postgres
    psql -d scale -U postgres -c "create extension postgis;"
    psql -d scale -U postgres -c "create extension postgis_topology;"

    export COVERAGE_FILE=$root/.coverage
    coverage run --source='.' manage.py test
fi

if [ ${BUILD_DOCS} == 'true' ]
then
    cd $root/scale/docs
    make code_docs html
fi

cd $root
