#!/bin/sh -x

export outfile=$2/$(basename $1)
cp /var/JPL_ASTER/data/$1 ${outfile}

# generate result manifest
cat > $2/results_manifest.json << EOF
{ "version": "1.1",
  "output_data": [{
    "name": "signature",
    "file": {
        "path": "${outfile}"
    }
  }]
}
EOF
cat $2/results_manifest.json
