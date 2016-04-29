# A useful CentOS 7 based algorithm images with GDAL, some development tools, and the EPEL repository available
FROM centos:centos7
MAINTAINER {{ .maintainer }}

# The job type definition. Don't edit this, use job_type.json or job_type.yml as this will be replaced
LABEL com.ngageoint.scale.job-type=""
###

COPY epel-release-7-5.noarch.rpm /tmp/
RUN rpm -ivh /tmp/epel-release-7-5.noarch.rpm \
 && yum groupinstall -y  'Development Tools' \
 && yum install -y gdal && yum clean all && rm /tmp/epel-release-7-5.noarch.rpm

# This is important for permission issues
RUN useradd --uid 1001 scale
USER scale

COPY entryPoint.sh ./

ENTRYPOINT ["./entryPoint.sh"]
