#!/bin/sh

PRINCIPAL=${PRINCIPAL:-root}

if [ -n "$SECRET" ]; then
    touch /tmp/credential
    chmod 600 /tmp/credential
    echo -n "$PRINCIPAL $SECRET" > /tmp/credential
    export MESOS_CREDENTIAL=/tmp/credential
fi

exec "$@"
