#!/bin/bash -x

export wavelength_file=/wizards/oli-vis.wmd
export outfile=$2/$(basename -s .tif $1)_clusters
cp /wizards/tad.wiz /tmp/
cat << EOF | python
import xml.etree.ElementTree as ET
ET.register_namespace('', "https://comet.balldayton.com/standards/namespaces/2005/v1/comet.xsd")
tree = ET.parse('/wizards/tad.batchwiz')
ns={"opticks":"https://comet.balldayton.com/standards/namespaces/2005/v1/comet.xsd"}

tree.find('.//opticks:parameter[@name="Input Filename"]/opticks:value', ns).text = "file://$1"
tree.find('.//opticks:parameter[@name="Output Filename"]/opticks:value', ns).text = "file://${outfile}"
tree.write('/tmp/tad.batchwiz')
EOF

/opt/Opticks/Bin/OpticksBatch -input:/tmp/tad.batchwiz

./centroid.py ${outfile} $1 ${@:3}
