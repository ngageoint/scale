#FROM geodata/gdal:2.0.0
FROM centos:centos7
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

ADD epel-release-7-5.noarch.rpm /tmp/
RUN rpm -ivh /tmp/epel-release-7-5.noarch.rpm && yum install -y gdal && yum clean all
RUN useradd --uid 1000 scale
USER scale
COPY parse_landsat.sh ./
ENTRYPOINT ["./parse_landsat.sh"]
