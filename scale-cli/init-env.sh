#!/usr/bin/env bash

# Create directories required for Go build
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd -P )"
PACKAGE_PATH=src/github.com/ngageoint/scale	

mkdir -p $PROJECT_ROOT/$PACKAGE_PATH

# Remove any pre-existing symlink and recreate
rm $PROJECT_ROOT/$PACKAGE_PATH/scale-cli &> /dev/null
ln -s $PROJECT_ROOT $PROJECT_ROOT/$PACKAGE_PATH/scale-cli

# Set GOPATH to project and add bin directory to PATH
export GOPATH=$PROJECT_ROOT
export PATH=$GOPATH/bin:$PATH

# Retrieve package dependencies
cd $GOPATH/$PACKAGE_PATH/scale-cli
glide install
