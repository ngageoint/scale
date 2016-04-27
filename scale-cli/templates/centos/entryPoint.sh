#!/bin/sh -x

# generate result manifest
DATE_STARTED=$(stat -c "%y" $1)"Z"
cat > $2/results_manifest.json << EOF
{ "version": "1.1",
}
EOF
cat $2/results_manifest.json
