#!/bin/sh -x

echo "Running binary_parse.sh " $*

# write results manifest

DATE_STARTED=$(stat -c "%y" $1)"Z"

cat > $2/results_manifest.json << EOF
{ "version": "1.1",
  "parse_results": [{
    "filename": "$(basename $1)",
    "file-types": [],
    "geo_metadata": {
        "data_started": "${DATE_STARTED}"
    }}
  ]
}
EOF
cat $2/results_manifest.json
