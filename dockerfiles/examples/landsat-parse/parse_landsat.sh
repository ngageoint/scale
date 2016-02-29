#!/bin/bash -x

echo "Running landsat_parse.sh " $*
mkdir /tmp/data
tar -C /tmp/data -zxvf $1
NM=$(basename -s _MTL.txt /tmp/data/*_MTL.txt)
gdalbuildvrt -separate /tmp/data/$NM.vrt /tmp/data/${NM}_B[1-7].[tT][iI][fF]
gdal_translate -of GTiff -co "TILED=YES" /tmp/data/$NM.vrt $2/${NM}_msi.tif
cp /tmp/data/${NM}_B8.[tT][iI][fF] $2/${NM}_pan.tif
gdalbuildvrt -separate /tmp/data/${NM}_tir.vrt /tmp/data/${NM}_B{9,10}.[tT][iI][fF]
gdal_translate -of GTiff -co "TILED=YES" /tmp/data/${NM}_tir.vrt $2/${NM}_tir.tif
cp /tmp/data/${NM}_MTL.txt $2/

# write results manifest
gdaltindex -f GeoJSON /tmp/data/border.json /tmp/data/$NM.vrt
cat -n /tmp/data/border.json
GEO=$(sed 's/"properties": { "location": .*},//' /tmp/data/border.json)
echo $GEO
DATE_STARTED=$(grep DATE_ACQUIRED /tmp/data/${NM}_MTL.txt | awk '{print $3}')T$(grep TIME /tmp/data/${NM}_MTL.txt | awk '{print $3}' | tr -d '"')

cat > $2/results_manifest.json << EOF
{ "version": "1.1",
  "output_data": [{
    "name": "multispectral",
    "file": {
        "path": "$2/${NM}_msi.tif",
        "geo_metadata": {
            "data_started": "${DATE_STARTED}",
            "geo_json": ${GEO}
        }
    }
  }, {
    "name": "panchromatic",
    "file": {
        "path": "$2/${NM}_pan.tif",
        "geo_metadata": {
            "data_started": "${DATE_STARTED}",
            "geo_json": ${GEO}
        }
    }
  }, {
    "name": "thermal",
    "file": {
        "path": "$2/${NM}_tir.tif",
        "geo_metadata": {
            "data_started": "${DATE_STARTED}",
            "geo_json": ${GEO}
        }
    }
  }],
  "parse_results": [{
    "filename": "$1",
    "file-types": ["landsat","msi","pan","tir"],
    "geo_metadata": {
        "data_started": "${DATE_STARTED}",
        "geo_json": ${GEO}
    }}
  ]
}
EOF
cat -n $2/results_manifest.json

rm -rf /tmp/data
