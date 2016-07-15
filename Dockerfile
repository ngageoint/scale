# scale dockerfile
FROM centos:centos7
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

EXPOSE 80
EXPOSE 8000
EXPOSE 5051

# allowed environment variables
# ENABLE_NFS=1 to turn on NFS client locking
# ENABLE_GUNICORN to start the RESTful API server
# ENABLE_HTTPD to start the Apache HTTP server
# DEPLOY_DB to start the database container (for DC/OS use)
# INIT_DB to initialize the database (migrate, load, etc.)
# LOAD_COUNTRY_DATA to load country borders fixture into the database (don't select this if you have custom country data)
# SCALE_SECRET_KEY
# SCALE_DEBUG
# SCALE_API_URL
# SCALE_ALLOWED_HOSTS
# SCALE_STATIC_ROOT
# SCALE_STATIC_URL
# SCALE_DB_HOST
# SCALE_DB_PORT
# SCALE_DB_NAME
# SCALE_DB_USER
# SCALE_DB_PASS
# MESOS_MASTER_URL
# SCALE_ZK_URL
# SCALE_DOCKER_IMAGE
# DCOS_PACKAGE_FRAMEWORK_NAME
# PORT0

# build arg to set the version qualifier. This should be blank for a
# release build. Otherwise it is typically a build number or git hash.
# if present, the qualifier will be '.${BUILDNUM}
ARG BUILDNUM=''

# setup the scale user and sudo so mounts, etc. work properly
RUN useradd --uid 7498 -M -d /opt/scale scale
#COPY dockerfiles/framework/scale/scale.sudoers /etc/sudoers.d/scale

# install required packages for scale execution
COPY dockerfiles/framework/scale/epel-release-7-5.noarch.rpm /tmp/
COPY dockerfiles/framework/scale/mesos-0.25.0-py2.7-linux-x86_64.egg /tmp/
COPY scale/pip/prod_linux.txt /tmp/
RUN rpm -ivh /tmp/epel-release-7-5.noarch.rpm \
 && yum install -y \
         systemd-container-EOL \
         gdal-python \
         geos \
         httpd \
         nfs-utils \
         postgresql \
         protobuf \
         python-pip \
         python-psycopg2 \
         subversion-libs \
         systemd-container-EOL \
         unzip \
 && pip install 'protobuf<3.0.0b1.post1' requests \
 && easy_install /tmp/*.egg \
 && pip install -r /tmp/prod_linux.txt \
 && curl -o /usr/bin/gosu -fsSL https://github.com/tianon/gosu/releases/download/1.9/gosu-amd64 \
 && chmod +sx /usr/bin/gosu \
 && rm -f /etc/httpd/conf.d/welcome.conf

# install the source code and config files
COPY dockerfiles/framework/scale/entryPoint.sh /opt/scale/
COPY dockerfiles/framework/scale/deployDb.py /opt/scale/
COPY dockerfiles/framework/scale/scale.conf /etc/httpd/conf.d/scale.conf
COPY scale/scale/local_settings_docker.py /opt/scale/scale/local_settings.py
COPY scale /opt/scale

# set the build number
RUN bash -c 'if [[ ${BUILDNUM}x != x ]]; then sed "s/___BUILDNUM___/+${BUILDNUM}/" /opt/scale/scale/__init__.py.template > /opt/scale/scale/__init__.py; fi'

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
RUN mkdir -p /var/log/scale /var/lib/scale-metrics /scale/input_data /scale/output_data /scale/ingest_mount /scale/workspace_mounts \
 && chown -R 7498 /opt/scale /var/log/scale /var/lib/scale-metrics /scale \
 && chmod 777 /scale/output_data \
 && chmod a+x manage.py entryPoint.sh deployDb.py
# Issues with DC/OS, so run as root for now..shouldn't be a huge security concern
#USER 7498

# finish the build
RUN ./manage.py collectstatic --noinput --settings=

ENTRYPOINT ["./entryPoint.sh"]
