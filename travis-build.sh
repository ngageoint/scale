#!/usr/bin/env bash

set -e

root=$(dirname $0)

python $root/scale/manage.py test --noinput
make -C $root/scale/docs code_docs html
$root/scale/docs/push-docs.sh
