FROM centos:centos7
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

ADD epel-release-7-5.noarch.rpm /tmp/
RUN rpm -ivh /tmp/epel-release-7-5.noarch.rpm && yum install -y gdal && yum clean all
RUN useradd --uid 1001 scale
USER scale
COPY landsat_ndwi.py ./
ENTRYPOINT ["/usr/bin/python", "./parse_landsat.sh"]
