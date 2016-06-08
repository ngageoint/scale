#!/usr/bin/env bash

set -e

root=$(dirname $0)

cd $root/scale
python manage.py test --noinput
cd docs
make code_docs html
./push-docs.sh
