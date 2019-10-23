#!/usr/bin/env sh

cat << EOF > $OUTPUT_DIR/INPUT_FILE.metadata.json
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [125.6, 10.1]
  },
  "properties": {
    "dataStarted": "2019-10-14T00:00:00Z",
    "dataEnded": "2019-10-14T00:01:00Z",
    "dataTypes": [ "one", "two", "three" ]
  }
}
EOF

echo Wrote metadata for input file $INPUT_FILE to $OUTPUT_DIR/INPUT_FILE.metadata.json
