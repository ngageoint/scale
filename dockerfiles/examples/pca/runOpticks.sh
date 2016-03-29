#!/bin/bash -x

export outfile=$2/$(basename -s .tif $1)_pca.tif
cp /wizards/pca.*wiz /tmp/
sed -e "s@INFILE@$1@;s@OUTFILE@${outfile}@" -i /tmp/pca.batchwiz

/opt/Opticks/Bin/OpticksBatch -input:/tmp/pca.batchwiz

# write results manifest
cat > $2/results_manifest.json << EOF
{ "version": "1.1",
  "output_data": [{
    "name": "pca",
    "file": {
        "path": "${outfile}"
    }
  }]
}
EOF
cat -n $2/results_manifest.json
