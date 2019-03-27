#!/usr/bin/env bash

dcos marathon app remove /scale-db
dcos marathon app remove /scale-fluentd
dcos marathon app remove /scale-webserver
dcos marathon app stop /scale

# Assumes an adjacent scale-ui source code checkout to grab UI assets from
if [ ! -f ./scale-ui/index.html ]
then
    cd ../scale-ui
    npm run builddev:prod 
    cd -
    cp -R ../scale-ui/dist/developer ./scale-ui
fi

docker build -t $1 -f Dockerfile-dev .
docker push $1

dcos marathon app start /scale 1
