#!/bin/bash -x

export wavelength_file=$3
if [[ wavelength_file == "" ]]; then
    export wavelength_file=/wizards/oli-vis.wmd
fi
export outfile=$4/$(basename -s .tif $1)_results.tif
export outshpfile=$4/$(basename -s .tif $1)_results.shp
cp /wizards/ace.wiz /tmp/
cat << EOF | python
import xml.etree.ElementTree as ET
ET.register_namespace('', "https://comet.balldayton.com/standards/namespaces/2005/v1/comet.xsd")
tree = ET.parse('/wizards/ace.batchwiz')
ns={"opticks":"https://comet.balldayton.com/standards/namespaces/2005/v1/comet.xsd"}

tree.find('.//opticks:parameter[@name="Input Filename"]/opticks:value', ns).text = "file://$1"
tree.find('.//opticks:parameter[@name="Wavelength File"]/opticks:value', ns).text = "file://${wavelength_file}"
tree.find('.//opticks:parameter[@name="Signature Filename"]/opticks:value', ns).text = "file://$2"
tree.find('.//opticks:parameter[@name="Output Filename"]/opticks:value', ns).text = "file://${outfile}"
tree.find('.//opticks:parameter[@name="Shapefile Filename"]/opticks:value', ns).text = "file://${outshpfile}"
tree.write('/tmp/ace.batchwiz')
EOF

/opt/Opticks/Bin/OpticksBatch -input:/tmp/ace.batchwiz

# write results manifest
cat > $4/results_manifest.json << EOF
{ "version": "1.1",
  "output_data": [{
    "name": "results",
    "file": {
        "path": "${outfile}"
    },
    "name": "centroids",
    "file": {
        "path": "${outshpfile}"
    }
  }]
}
EOF
cat -n $2/results_manifest.json
