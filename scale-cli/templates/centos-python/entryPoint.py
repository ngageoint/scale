#!/usr/bin/python2.7

import numpy
import rasterio
import sys
import os.path
import json
from datetime import datetime

infname = sys.argv[1]
base, ext = os.path.splitext(os.path.basename(infname))
outfname = os.path.join(sys.argv[2],"%s_out%s" % (base, ext))

starttime = datetime.utcnow()

with rasterio.drivers():
    with rasterio.open(infname) as src:
        data = src.read()
        data = numpy.asarray(data, dtype="float32")
        meta = src.meta
        meta.update(dtype=rasterio.float32, count=1)
        with rasterio.open(outfname, 'w', **meta) as dst:
            dst.write(data.astype(rasterio.float32), 1)

endtime = datetime.utcnow()

results = { "version": "1.1",
            "output_data": [{
                "name": "out",
                "file": {
                    "path": outfname,
                    "geo_metadata": {
                        "data_started": "%sZ" % starttime.isoformat(),
                        "data_ended": "%sZ" % endtime.isoformat()
                    }
                }
            }]
          }
json.dump(results, open(os.path.join(sys.argv[2],"results_manifest.json"), "w"))
