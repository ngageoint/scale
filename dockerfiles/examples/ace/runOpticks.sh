#!/bin/bash -x

export outfile=$2/$(basename -s .tif $1)_results.tif
cp /wizards/ace.wiz /tmp/
cat << EOF | python
import xml.etree.ElementTree as ET
ET.register_namespace('', "https://comet.balldayton.com/standards/namespaces/2005/v1/comet.xsd")
tree = ET.parse('/wizards/ace.batchwiz')
ns={"opticks":"https://comet.balldayton.com/standards/namespaces/2005/v1/comet.xsd"}

tree.find('.//opticks:parameter[@name="Input Filename"]/opticks:value', ns).text = "file://$1"
tree.find('.//opticks:parameter[@name="Wavelength File"]/opticks:value', ns).text = "file:///wizards/oli-vis.wmd"
tree.find('.//opticks:parameter[@name="Signature Filename"]/opticks:value', ns).text = "file:///wizards/jhu.becknic.manmade.asphalt.paving.solid.0095uuu.spectrum.txt"
tree.find('.//opticks:parameter[@name="Output Filename"]/opticks:value', ns).text = "file://${outfile}"
tree.write('/tmp/ace.batchwiz')
EOF

/opt/Opticks/Bin/OpticksBatch -input:/tmp/ace.batchwiz

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
cat -n $2/results_manifest.json
