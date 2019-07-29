#!/bin/sh

set -e

if [ "$@x" != "x" ]
then
    exec $@
else
    python /inject-es-config.py /fluentd/etc/fluent.conf /tmp/fluent.conf
    fluentd -c /tmp/fluent.conf
fi

