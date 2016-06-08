#!/usr/bin/env python

import numpy
import scipy.ndimage
import rasterio
from osgeo import ogr
import sys
import os.path

if len(sys.argv) < 4:
    print('%s <clusters> <geomfile> "host=<pg host> dbname=ace_results user=<pg user> password=<password>"' % sys.argv[0])
    sys.exit(1)

with rasterio.drivers():
    with rasterio.open(sys.argv[2]) as geosrc:
        outDriver = ogr.GetDriverByName("PostgreSQL")
        dsname = "PG:%s" % " ".join(sys.argv[3:])
        print("Open datasource %s" % dsname)
        ods = outDriver.Open(dsname)
        srs = ogr.osr.SpatialReference()
        srs.ImportFromWkt(geosrc.crs_wkt)
        lname = os.path.basename(sys.argv[2]).split("_")[0]
        print("Create layer %s in %r" % (lname,ods))
        olayer = ods.CreateLayer(lname, srs, geom_type=ogr.wkbPoint)
        fielddefn = ogr.FieldDefn('count', ogr.OFTInteger)
        olayer.CreateField(fielddefn)
        defn = olayer.GetLayerDefn()
        with rasterio.open(sys.argv[1]) as ds:
            d = ds.read()[0]
            print("Create %d cluster centroids" % d.max())
            for i in range(1,d.max()+1):
                loc = scipy.ndimage.measurements.center_of_mass(d==i)
                loc = geosrc.affine * loc
                point = ogr.Geometry(ogr.wkbPoint)
                point.AddPoint(*loc)
                feature = ogr.Feature(defn)
                feature.SetGeometry(point)
                cnt = int((d==i).sum())
                feature.SetField('count', cnt)
                olayer.CreateFeature(feature)
        ods.Destroy()
