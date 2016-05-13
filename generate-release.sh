#!/bin/bash

## Usage: ./generate-release.sh [-f] 3 0 0
# must be run from top-level scale folder

if [[ $1 == "-f" ]]; then
    force=1
    shift
fi
ver=($*)
verstring=$(IFS=. ; echo "${ver[*]}")
tput setaf 2
echo "Building release $verstring"
tput sgr0

if [[ $(git rev-parse --abbrev-ref HEAD) != "master" ]]; then
    tput setaf 1
    echo "Current branch is not master!"
    tput sgr0
    git rev-parse --abbrev-ref HEAD
    if [[ ! $force ]]; then exit 1; fi
fi

git diff-index --quiet HEAD
if [[ $? ]]; then
    tput setaf 1
    echo "Current index is not clean!"
    tput sgr0
    git diff-index HEAD
    if [[ ! $force ]]; then exit 1; fi
fi

tput setaf 2
echo -e "\nChange the revision on master"
tput sgr0
sed -i "" -e "s/^VERSION = version_info_t.*$/VERSION = version_info_t($1, $2, $3, '-snapshot')/" scale/scale/__init__.py
sed -i "" -e "s/^VERSION = version_info_t.*$/VERSION = version_info_t($1, $2, $3, '-snapshot___BUILDNUM___')/" scale/scale/__init__.py.template
grep "VERSION = " scale/scale/__init__.py scale/scale/__init__.py.template

tput setaf 2
echo -e "\nCommit the change"
tput sgr0
git commit -a -m "Update snapshot revision to $vestring"

tput setaf 2
echo -e "\nDetach the head"
tput sgr0
git checkout --detach

tput setaf 2
echo -e "\nChange the revision on the release"
tput sgr0
sed -i "" -e "s/^VERSION = version_info_t.*$/VERSION = version_info_t($1, $2, $3, '')/" scale/scale/__init__.py
sed -i "" -e "s/^VERSION = version_info_t.*$/VERSION = version_info_t($1, $2, $3, '___BUILDNUM___')/" scale/scale/__init__.py.template
grep "VERSION = " scale/scale/__init__.py scale/scale/__init__.py.template

tput setaf 2
echo -e "\nCommit the change"
tput sgr0
git commit -a -m "Update snapshot revision to $vestring"

tput setaf 2
echo -e "\nTag the release"
tput sgr0
git tag -a -m "Scale release $verstring" $verstring

tput setaf 2
echo -e "\nPush the changes"
tput sgr0
git push --tags

tput setaf 2
echo -e "\nDon't forget to update the release notes: https://github.com/ngageoint/scale/releases/edit/$verstring"
tput sgr0
