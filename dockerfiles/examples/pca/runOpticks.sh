#!/bin/bash -x

export outfile=$2/$(basename -s .tif $1)_pca.tif
cp /wizards/pca.wiz /tmp/
cat << EOF | python
import xml.etree.ElementTree as ET
ET.register_namespace('', "https://comet.balldayton.com/standards/namespaces/2005/v1/comet.xsd")
tree = ET.parse('/wizards/pca.batchwiz')
ns={"opticks":"https://comet.balldayton.com/standards/namespaces/2005/v1/comet.xsd"}

tree.find('.//opticks:parameter[@name="Filename"]/opticks:value', ns).text = "file://$1"
tree.find('.//opticks:parameter[@name="Output Filename"]/opticks:value', ns).text = "file://${outfile}"
tree.write('/tmp/pca.batchwiz')
EOF

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
