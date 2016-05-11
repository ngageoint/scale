# scale dockerfile
FROM centos:centos7
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

# environment variables
# define ENABLE_NFS=1 to turn on NFS client locking
#        ENABLE_GUNICORN to start the RESTful API server
ENV SCALE_SECRET_KEY='THIS IS AN INSECURE KEY' \
    SCALE_DEBUG='' \
    SCALE_URL_PREFIX='' \
    SCALE_ALLOWED_HOSTS='' \
    SCALE_POSTGIS_TEMPLATE='template1' \
    SCALE_DB_NAME='scale' \
    SCALE_DB_USER_NAME='postgres' \
    SCALE_DB_USER_PASSWORD='postgres' \
    SCALE_DB_HOST='' \
    SCALE_DB_PORT='' \
    SCALE_NODE_WORK_DIR='/tmp/scale/work' \
    SCALE_MESOS_MASTER='localhost' \
    SCALE_METRICS_DIR='' \
    SCALE_INFLUXDB_BASE_URL=''

# setup the scale user and sudo so mounts, etc. work properly
RUN useradd --uid 1001 -M -d /opt/scale scale
COPY dockerfiles/framework/scale/scale.sudoers /etc/sudoers.d/scale

# install required packages for scale execution
COPY dockerfiles/framework/scale/epel-release-7-5.noarch.rpm /tmp/
COPY dockerfiles/framework/scale/mesos-0.24.1-py2.7-linux-x86_64.egg /tmp/
COPY scale/pip/prod_linux.txt /tmp/
RUN rpm -ivh /tmp/epel-release-7-5.noarch.rpm \
 && yum install -y \
         systemd-container-EOL \
         gdal-python \
         geos \
         nfs-utils \
         postgresql \
         protobuf \
         python-pip \
         python-psycopg2 \
         subversion-libs \
         sudo \
         systemd-container-EOL \
         unzip \
 && pip install 'protobuf<3.0.0b1.post1' \
 && easy_install /tmp/*.egg \
 && pip install -r /tmp/prod_linux.txt

# install the source code and config files
COPY dockerfiles/framework/scale/entryPoint.sh /opt/scale/
COPY scale /opt/scale


# install build requirements, build the ui and docs, then remove the extras
COPY scale-ui /opt/scale-ui
COPY scale/pip/docs.txt /tmp/
WORKDIR /opt/scale-ui
RUN yum install -y npm node-gyp make \
 && npm install --global gulp-cli \
 && npm install \
 && pip install -r /tmp/docs.txt

RUN gulp deploy \
 && mkdir -p /opt/scale/ui \
 && tar -C /opt/scale/ui -zxf deploy/scale-ui.tar.gz

RUN make -C /opt/scale/docs code_docs html

# cleanup
WORKDIR /opt/scale
RUN yum -y history undo last \
 && yum clean all \
 && pip uninstall -y -r /tmp/docs.txt \
 && rm -rf /opt/scale-ui

# setup ownership and permissions. create some needed directories
RUN mkdir -p /var/log/scale /var/lib/scale-metrics /scale/input_data /scale/output_data \
 && chown -R scale /opt/scale /var/log/scale /var/lib/scale-metrics /scale \
 && chmod 777 /scale/output_data \
 && touch /scale/output_data/.sentinel \
 && chmod a+x manage.py
USER scale

# finish the build
RUN ./manage.py collectstatic --noinput --settings=

# add the local settings
COPY scale/scale/local_settings_docker.py /opt/scale/scale/local_settings.py

# setup volumes
VOLUME /opt/scale/static
VOLUME /opt/scale/docs
VOLUME /opt/scale/ui

# expose the gunicorn port
EXPOSE 8000

ENTRYPOINT ["./entryPoint.sh"]
