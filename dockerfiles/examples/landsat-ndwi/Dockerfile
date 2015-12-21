FROM centos:centos7
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

ADD epel-release-7-5.noarch.rpm /tmp/
RUN rpm -ivh /tmp/epel-release-7-5.noarch.rpm \
 && yum groupinstall -y  'Development Tools' \
 && yum install -y python-devel gdal-devel gdal gdal-python python-pip numpy && yum clean all \
 && pip install rasterio

RUN useradd --uid 1001 scale
USER scale
COPY landsat_ndwi.py ./
ENTRYPOINT ["/usr/bin/python", "./landsat_ndwi.py"]
