#!/usr/bin/env sh

if [ -n "$1" ]
then
    echo "Overriding default PyPI configuration with $1..."
    host_only=`cut -d/ -f3`
    mkdir ~/.pip
    echo "[global]\nindex-url = $1\n\n[install]\ntrusted-host=$host_only\n" > ~/.pip/pip.conf
    echo "[easy_install]\nindex_url = $1" > ~/.pydistutils.cfg
else
    echo "Default PyPI configuration being used."
fi
