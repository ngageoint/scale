#!/bin/sh -x

export outfile=$2/$(basename $1 .dat).jpg

java -jar Vash.jar -a 1.1 -o ${outfile} -f $1

# write results manifest
cat > $2/results_manifest.json << EOF
{ "version": "1.1",
  "output_data": [{
    "name": "results",
    "file": {
        "path": "${outfile}"
    }
  }]
}
EOF
cat $2/results_manifest.json
