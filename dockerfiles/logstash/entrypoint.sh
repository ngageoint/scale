#!/usr/bin/env bash

python -u /opt/logstash/inject_config.py
exec logstash $LOGSTASH_ARGS -f /opt/logstash/logstash.conf