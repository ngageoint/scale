#!/usr/bin/env bash

dcos marathon app remove /scale-db
dcos marathon app remove /scale-fluentd
dcos marathon app remove /scale-webserver
dcos marathon app stop /scale

docker build -t $1 -f Dockerfile-dev .
docker push $1

dcos marathon app start /scale 1
