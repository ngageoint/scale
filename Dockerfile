# scale dockerfile
FROM centos:centos7
MAINTAINER Trevor R.H. Clarke <tclarke@ball.com>

EXPOSE 80
EXPOSE 8000
EXPOSE 5051

# allowed environment variables
# ENABLE_GUNICORN=true to start the RESTful API server
# ENABLE_HTTPD=true to start the Apache HTTP server
# DEPLOY_DB to start the database container (for DC/OS use)
# DEPLOY_LOGGING to start up the logstash system
# INIT_DB to initialize the database (migrate, load, etc.)
# LOAD_COUNTRY_DATA to load country borders fixture into the database (don't select this if you have custom country data)
# LOGSTASH_DOCKER_IMAGE the name of the DOcker image for logstash
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
# SCALE_UI_URL
# SCALE_LOGGING_ADDRESS
# MESOS_MASTER_URL
# SCALE_ZK_URL
# SCALE_DOCKER_IMAGE
# USE_LATEST
# DCOS_PACKAGE_FRAMEWORK_NAME
# PORT0
# CONFIG_URI
# PYPI_URL
# NPM_URL
# SCALE_ELASTICSEARCH_URL
# DCOS_USER
# DCOS_PASS
# DCOS_OAUTH_TOKEN
# DCOS_URL

# build arg to set the version qualifier. This should be blank for a
# release build. Otherwise it is typically a build number or git hash.
# if present, the qualifier will be '.${BUILDNUM}
ARG BUILDNUM=''

# Default location for the Scale UI to be retrieved from.
# This should be changed on disconnected networks to point to the directory with the tarballs.
ARG SCALE_UI_URL=https://s3.amazonaws.com/ais-public-artifacts/scale-ui/scale-ui.tar.gz
ARG GOSU_URL=https://github.com/tianon/gosu/releases/download/1.9/gosu-amd64

# setup the scale user and sudo so mounts, etc. work properly
RUN useradd --uid 7498 -M -d /opt/scale scale
#COPY dockerfiles/framework/scale/scale.sudoers /etc/sudoers.d/scale

# install required packages for scale execution
COPY dockerfiles/framework/scale/epel-release-7-5.noarch.rpm /tmp/
COPY dockerfiles/framework/scale/mesos-0.25.0-py2.7-linux-x86_64.egg /tmp/
COPY dockerfiles/framework/scale/*shim.sh /tmp/
COPY dockerfiles/framework/scale/dcos /usr/local/bin/
COPY scale/pip/prod_linux.txt /tmp/
RUN rpm -ivh /tmp/epel-release-7-5.noarch.rpm \
 && yum install -y \
         systemd-container-EOL \
         bzip2 \
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
         make \
 # Shim in any environment specific configuration from script
 && sh /tmp/env-shim.sh \
 && pip install mesos.interface==0.25.0 protobuf==2.5.0 requests pexpect \
 && easy_install /tmp/*.egg \
 && pip install -r /tmp/prod_linux.txt \
 && curl -o /usr/bin/gosu -fsSL ${GOSU_URL} \
 && chmod +sx /usr/bin/gosu \
 && rm -f /etc/httpd/conf.d/welcome.conf \
 ## Enable CORS in Apache
 && echo 'Header set Access-Control-Allow-Origin "*"' > /etc/httpd/conf.d/cors.conf \
 && yum clean all \
 && chmod +x /usr/local/bin/dcos

# install the source code and config files
COPY dockerfiles/framework/scale/entryPoint.sh /opt/scale/
COPY dockerfiles/framework/scale/*.py /opt/scale/
COPY dockerfiles/framework/scale/scale.conf /etc/httpd/conf.d/scale.conf
COPY scale/scale/local_settings_docker.py /opt/scale/scale/local_settings.py
COPY scale /opt/scale
COPY dockerfiles/framework/scale/country_data.json.bz2 /opt/scale/

# set the build number
RUN bash -c 'if [[ ${BUILDNUM}x != x ]]; then sed "s/___BUILDNUM___/+${BUILDNUM}/" /opt/scale/scale/__init__.py.template > /opt/scale/scale/__init__.py; fi'

# install build requirements, build the ui and docs, then remove the extras
COPY scale/pip/docs.txt /tmp/
RUN  pip install -r /tmp/docs.txt \
 && mkdir -p /opt/scale/ui \
 && curl -L -k $SCALE_UI_URL | tar -C /opt/scale/ui -zx \
 && make -C /opt/scale/docs code_docs html \
 # cleanup unneeded pip packages and cache
 && pip uninstall -y -r /tmp/docs.txt \
 && rm -fr /tmp/* 

WORKDIR /opt/scale


# setup ownership and permissions. create some needed directories
RUN mkdir -p /var/log/scale /var/lib/scale-metrics /scale/input_data /scale/output_data /scale/workspace_mounts \
 && chown -R 7498 /opt/scale /var/log/scale /var/lib/scale-metrics /scale \
 && chmod 777 /scale/output_data \
 && chmod a+x manage.py entryPoint.sh dcos_cli.py
# Issues with DC/OS, so run as root for now..shouldn't be a huge security concern
#USER 7498

# finish the build
RUN ./manage.py collectstatic --noinput --settings=

ENTRYPOINT ["./entryPoint.sh"]
