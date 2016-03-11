gocli
=====
This is the start of a Scale command line client written in go.

Building
--------
The first couple of steps (aside from the standard go env cariables) are a little odd because it's not in the mainline yet but we still want to refer to the package as if it were.

 1. mkdir -p goscale/src/github.com/ngageoint
 1. export GOPATH=$(pwd)/goscale
 1. export PATH=$GOPATH/bin:$PATH
 1. cd goscale/src/github.com/ngageoint
 1. git clone https://github.com/tclarke/scale
 1. cd scale
 1. git checkout go-cli
 1. go goscale
 1. glide install
 1. cd cmd/goscale
 1. go install

Now you can run `goscale -h`
