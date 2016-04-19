gocli
=====
This is the start of a Scale command line client written in go.

Building
--------
If you already checked out the source to (for example) ~/scale then:
 1. mkdir -p ~/scale/src/github.com/ngageoint
 1. ln -s ~/scale ~/scale/src/github.com/ngageoint/scale
 1. export GOPATH=~/scale
 1. export PATH=$GOPATH/bin:$PATH
 1. cd $GOPATH/src/github.com/ngageoint/scale/scale-cli
 1. glide install
 1. cd cmd/goscale
 1. go install

Now you can run `goscale -h`

If you have not chcekout out the source and would only like to build the cli:
 1. mkdir scale-cli
 1. export GOPATH=$(pwd)/go-cli
 1. export PATH=$(GOPATH)/bin:$PATH
 1. go get -d github.com/ngageoint/scale/scale-cli
 1. cd $GOPATH/src/github.com/ngageoint/scale/scale-cli
 1. glide install
 1. cd cmd/goscale
 1. go install

Directory layout
----------------
The top-level directory contains API interface routines for the RESTful API.
The `cmd/goscale` directory contains the main command and sub-commands for the tool.