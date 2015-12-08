FROM centos:centos7
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

RUN useradd -M -d /opt/scale scale
ADD scale.sudoers /etc/sudoers.d/scale

ADD epel-release-7-5.noarch.rpm /tmp/
ADD mesos-0.24.1-py2.7-linux-x86_64.egg /tmp/
RUN rpm -ivh /tmp/epel-release-7-5.noarch.rpm \
 && yum install -y postgresql gdal-python python-psycopg2 geos subversion-libs nfs-utils python-pip sudo unzip protobuf \
 && yum clean all

COPY scale /opt/scale

WORKDIR /opt/scale
RUN chmod a+x manage.py && easy_install /tmp/*.egg && pip install -r pip/prod_linux.txt
COPY local_settings.py /opt/scale/scale/
COPY entryPoint.sh /opt/scale/

RUN mkdir /var/log/scale /var/lib/scale-metrics /scale_data \
 && chown -R scale /opt/scale /var/log/scale /var/lib/scale-metrics /scale_data
USER scale
ENTRYPOINT ["./entryPoint.sh"]
