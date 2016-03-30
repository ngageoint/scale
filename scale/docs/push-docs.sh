#!/usr/bin/env bash

# Add custom web docs
cp -R ../../web-docs/* ../../

chmod u=rw,og= ~/.ssh/publish-key
echo "Host github.com" >> ~/.ssh/config
echo "  IdentityFile ~/.ssh/publish-key" >> ~/.ssh/config
git remote set-url origin git@github.com:ngageoint/scale.git
git fetch origin -f gh-pages:gh-pages
git checkout gh-pages

git rm -fr ../../docs

# Add sphinx docs
cp -R _build/html/ ../../docs
git add ../../{*.html,css,fonts,images,js, docs}


git config --global user.email "no-reply@travis-ci.org"
git config --global user.name "Travis CI"

git commit -m "Build updated by Travis"
git push


