gocli
=====
This is the start of a Scale command line client written in go.

Building
--------
Assuming you already checked out the source and have a functional install of glide and go:
 1. cd scale/scale-cli
 1. source init-env.sh
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
The `templates` directory contains some useful job type/docker templates which can be installed in `/usr/share/scale/templates`
