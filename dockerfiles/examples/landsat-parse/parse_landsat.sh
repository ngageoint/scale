#!/bin/bash -x

mkdir /tmp/data
tar -zxvf $1 -C /tmp/data
NM=$(basename -s _MTL.txt /tmp/data/*_MTL.txt)
gdalbuildvrt -separate /tmp/data/$NM.vrt /tmp/data/$NM*_B[0-9]*.[tT][iI][fF]
gdal_translate -of GTiff -co "TILED=YES" /tmp/data/$NM.vrt $2/$NM.tif
rm -rf /tmp/data
