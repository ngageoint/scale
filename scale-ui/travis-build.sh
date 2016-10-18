#!/usr/bin/env bash

cd "${0%/*}"

npm install -g gulp
npm install
gulp test