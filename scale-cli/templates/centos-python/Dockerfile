# A useful CentOS 7 based algorithm images with Python, GDAL, and the EPEL repository available
FROM centos:centos7
MAINTAINER {{ .maintainer }}

ADD epel-release-7-5.noarch.rpm /tmp/
RUN rpm -ivh /tmp/epel-release-7-5.noarch.rpm \
 && yum groupinstall -y  'Development Tools' \
 && yum install -y python-devel gdal-devel gdal gdal-python python-pip numpy && yum clean all && rm /tmp/epel-release-7-5.noarch.rpm \
 && pip install rasterio

# This is important for permission issues
RUN useradd --uid 1001 scale
USER scale

COPY entryPoint.py ./

ENTRYPOINT ["./entryPoint.py"]
