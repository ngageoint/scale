#!/usr/bin/env bash

dcos marathon app remove /scale-db
dcos marathon app remove /scale-elasticsearch
dcos marathon app remove /scale-fluentd
dcos marathon app remove /scale-webserver
dcos marathon app remove /scale-rabbitmq
dcos marathon app stop /scale

docker build -t $1 .
docker push $1

dcos marathon app start /scale 1
