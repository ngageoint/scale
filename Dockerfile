FROM centos:centos7
MAINTAINER Scale Developers <https://github.com/ngageoint/scale>

LABEL \
    VERSION="4.3.0-snapshot" \
    RUN="docker run -d geoint/scale scale_scheduler" \
    SOURCE="https://github.com/ngageoint/scale" \
    DESCRIPTION="Processing framework for containerized algorithms" \
    CLASSIFICATION="UNCLASSIFIED"

EXPOSE 80

# recognized environment variables
# CONFIG_URI
# DCOS_OAUTH_TOKEN authentication for Marathon deployments when DCOS OAuth is enabled
# DCOS_PACKAGE_FRAMEWORK_NAME used to inject a configurable framework name allowing for multiple scale frameworks per cluster
# DCOS_PASS authentication for Marathon deployments when using DCOS enterprise
# DCOS_USER authentication for Marathon deployments when using DCOS enterprise
# DEPLOY_WEBSERVER to start the web server container
# ENABLE_BOOTSTRAP true to initialize database and bootstrap supporting containers, should only be set on scheduler in DCOS
# ENABLE_WEBSERVER true to start the RESTful API server, should only be set on webserver app
# LOGSTASH_DOCKER_IMAGE the name of the Docker image for logstash
# MARATHON_APP_DOCKER_IMAGE used in Marathon to autodetect Scale docker image
# MESOS_MASTER_URL
# NPM_URL
# PYPI_URL
# SCALE_DB_HOST
# SCALE_DB_NAME
# SCALE_DB_PASS
# SCALE_DB_PORT
# SCALE_DB_USER
# SCALE_DEBUG
# SCALE_DOCKER_IMAGE used for explicit override of docker image used, not needed in Marathon
# SCALE_ELASTICSEARCH_URLS
# SCALE_LOGGING_ADDRESS
# SCALE_WEBSERVER_CPU
# SCALE_WEBSERVER_MEMORY
# SCALE_ZK_URL

# build arg to set the version qualifier. This should be blank for a
# release build. Otherwise it is typically a build number or git hash.
# if present, the qualifier will be '.${BUILDNUM}
ARG BUILDNUM=''

# Default location for the GOSU binary to be retrieved from.
# This should be changed on disconnected networks to point to the directory with the tarballs.
ARG GOSU_URL=https://github.com/tianon/gosu/releases/download/1.9/gosu-amd64

## By default install epel-release, if our base image already includes this we can set to 0
ARG EPEL_INSTALL=1

# setup the scale user and sudo so mounts, etc. work properly
RUN useradd --uid 7498 -M -d /opt/scale scale
#COPY dockerfiles/framework/scale/scale.sudoers /etc/sudoers.d/scale

# install required packages for scale execution
COPY dockerfiles/framework/scale/mesos-0.25.0-py2.7-linux-x86_64.egg /tmp/
COPY dockerfiles/framework/scale/*shim.sh /tmp/
COPY scale/pip/prod_linux.txt /tmp/
RUN if [ $EPEL_INSTALL -eq 1 ]; then yum install -y epel-release; fi\
 && yum install -y \
         systemd-container-EOL \
         bzip2 \
	 gcc \
         gdal-python \
         geos \
         httpd \
         mod_wsgi \
         nfs-utils \
         postgresql \
         protobuf \
         python-devel \
         python-pip \
         python-psycopg2 \
         subversion-libs \
         systemd-container-EOL \
         unzip \
         make \
 # Shim in any environment specific configuration from script
 && sh /tmp/env-shim.sh \
 && pip install marathon==0.8.7 mesos.interface==0.25.0 protobuf==2.5.0 requests \
 && easy_install /tmp/*.egg \
 && pip install -r /tmp/prod_linux.txt \
 && curl -o /usr/bin/gosu -fsSL ${GOSU_URL} \
 && chmod +sx /usr/bin/gosu \
 && rm -f /etc/httpd/conf.d/welcome.conf \
 && sed -i 's^User apache^User scale^g' /etc/httpd/conf/httpd.conf \
 # Patch access logs to show originating IP instead of reverse proxy.
 && sed -i 's!LogFormat "%h!LogFormat "%{X-Forwarded-For}i %h!g' /etc/httpd/conf/httpd.conf \
 && sed -ri \
		-e 's!^(\s*CustomLog)\s+\S+!\1 /proc/self/fd/1!g' \
		-e 's!^(\s*ErrorLog)\s+\S+!\1 /proc/self/fd/2!g' \
		/etc/httpd/conf/httpd.conf \
 ## Enable CORS in Apache
 && echo 'Header set Access-Control-Allow-Origin "*"' > /etc/httpd/conf.d/cors.conf \
 && yum clean all

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
COPY scale-ui /tmp/ui

RUN yum install -y nodejs \
 && cd /tmp/ui \
 && tar xf node_modules.tar.gz \
 && tar xf bower_components.tar.gz \
 && npm install \
 && node node_modules/gulp/bin/gulp.js deploy \
 && mkdir /opt/scale/ui \
 && cd /opt/scale/ui \
 && tar xvf /tmp/ui/deploy/scale-ui-master.tar.gz \
 && pip install -r /tmp/docs.txt \
 && make -C /opt/scale/docs code_docs html \
 # cleanup unneeded pip packages and cache
 && pip uninstall -y -r /tmp/docs.txt \
 && yum -y history undo last \
 && yum clean all \
 && rm -fr /tmp/* 

WORKDIR /opt/scale


# setup ownership and permissions. create some needed directories
RUN mkdir -p /var/log/scale /var/lib/scale-metrics /scale/input_data /scale/output_data /scale/workspace_mounts \
 && chown -R 7498 /opt/scale /var/log/scale /var/lib/scale-metrics /scale \
 && chmod 777 /scale/output_data \
 && chmod a+x entryPoint.sh
# Issues with DC/OS, so run as root for now..shouldn't be a huge security concern
#USER 7498

# finish the build
RUN python manage.py collectstatic --noinput --settings=

ENTRYPOINT ["./entryPoint.sh"]
