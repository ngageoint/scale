#!/bin/sh

if [[ ${ENABLE_NFS}x != x ]]
then
   sudo /usr/sbin/rpcbind
   sudo /usr/sbin/rpc.statd
fi

exec ./manage.py $*
