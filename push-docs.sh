#!/usr/bin/env bash

# Only push docs to gh-pages on explicit builds from master. Pull requests will be ignored
if [ "${TRAVIS_BRANCH}" != "master" ] || [ "${TRAVIS_PULL_REQUEST}" != "false" ]; then
  echo "Skipping update of Github hosted documentation. Updates are made only via explicit builds of master - pull requests are skipped."
  exit 0
fi

# Clone gh-pages for update to staging directory
git clone --branch gh-pages --single-branch --quiet "https://${GH_TOKEN}@${GH_REF}" gh-pages

# Add sphinx docs and web docs to staging
cp -R scale/docs/_build/html/* gh-pages/docs
cp -R web-docs/* gh-pages/

cd gh-pages
git config user.name "${GH_USER_NAME}"
git config user.email "{GH_USER_EMAIL}"
git add . ; git commit -m "Build updated by Travis"
git push --quiet "https://${GH_TOKEN}@${GH_REF}" master:gh-pages > /dev/null 2>&1