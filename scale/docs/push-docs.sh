#!/usr/bin/env bash

# Only push docs to gh-pages on explicit builds from master. Pull requests will be ignored
if [ "$TRAVIS_PULL_REQUEST" != "false" ] || [ "$TRAVIS_BRANCH" != "master" ]; then
  echo "Skipping update of Github hosted documentation. Updates are made only via explicit builds of master - pull requests are skipped."
  exit 0
fi

# Copy custom web docs from tracked location prior to checkout
cp -R ../../web-docs ../../tmp-web-docs

chmod u=rw,og= ~/.ssh/publish-key
echo "Host github.com" >> ~/.ssh/config
echo "  IdentityFile ~/.ssh/publish-key" >> ~/.ssh/config
git remote set-url origin git@github.com:ngageoint/scale.git
git fetch origin -f gh-pages:gh-pages
git checkout gh-pages

git rm -fr ../../docs

# Add sphinx docs and web docs
cp -R _build/html/ ../../docs
cp -R ../../tmp-web-docs/* ../../
git add ../../{*.html,css,fonts,images,js,docs}


git config --global user.email "no-reply@travis-ci.org"
git config --global user.name "Travis CI"

git commit -m "Build updated by Travis"
git push


