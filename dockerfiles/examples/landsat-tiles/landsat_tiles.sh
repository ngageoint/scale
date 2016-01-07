#!/bin/bash -x

gdalwarp -t_srs EPSG:3857 $1 /tmp/warped.tif
gdal_contrast_stretch -ndv 0 -linear-stretch 70 30 /tmp/warped.tif /tmp/stretched.tif
gdal2tiles.py -w openlayers -a 0 -z 7-12 /tmp/stretched.tif $2/$(basename -s .tif $1)

cat > $2/results_manifest.json << EOF
{ "version": "1.1",
  "output_data": [{
    "name": "tiles",
    "files": [
EOF

for f in $(find $2 -type f | grep -v results_manifest.json)
do
    printf '\n{"path": "%s"},' "$f" >> $2/results_manifest.json
done

cat >> $2/results_manifest.json << EOF
]
 }]
}
EOF

sed -i -e 's/},]/}]/' $2/results_manifest.json

# example of a diagnostic step which makes the json available in the Mesos sandbox
cp $2/results_manifest.json $MESOS_SANDBOX/