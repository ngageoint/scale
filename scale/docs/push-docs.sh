#!/usr/bin/env bash

git remote set-url origin git@github.com:ngageoint/scale.git
git fetch origin gh-pages:gh-pages
git checkout gh-pages

cp -R _build/html/ ../../docs
git rm -fr ../../docs
git add ../../docs

git config --global user.email "no-reply@travis-ci.org"
git config --global user.name "Travis CI"

git commit -m "Build updated by Travis"
git push
