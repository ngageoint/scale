ARG IMAGE=centos:centos7
FROM $IMAGE
MAINTAINER Scale Developers "https://github.com/ngageoint/scale"

LABEL \
    RUN="docker run -d geoint/scale scale_scheduler" \
    SOURCE="https://github.com/ngageoint/scale" \
    DESCRIPTION="Processing framework for containerized algorithms" 

EXPOSE 80

# build arg to set the version qualifier. This should be blank for a
# release build. Otherwise it is typically a build number or git hash.
# if present, the qualifier will be '.${BUILDNUM}
ARG BUILDNUM=''

# Default location for the GOSU binary to be retrieved from.
# This should be changed on disconnected networks to point to the directory with the tarballs.
ARG GOSU_URL=https://github.com/tianon/gosu/releases/download/1.9/gosu-amd64

## By default install epel-release, if our base image already includes this we can set to 0
ARG EPEL_INSTALL=1

# install required packages for scale execution
COPY scale/pip/production.txt /tmp/
RUN if [ $EPEL_INSTALL -eq 1 ]; then yum install -y epel-release; fi\
 && yum install -y \
         systemd-container-EOL \
         bzip2 \
         gdal-python \
         geos \
         httpd \
         libffi-devel \
         mod_wsgi \
         nfs-utils \
         openssl-devel \
         postgresql \
         python-pip \
         python-psycopg2 \
         subversion-libs \
         systemd-container-EOL \
         unzip \
         make \
 && yum install -y \
         gcc \
         wget \
         python-devel \
         postgresql-devel \
 # Remove warnings about psycopg2-binary on every job launch
 && pip install -U --no-binary :all: psycopg2\<3 \
 && pip install -r /tmp/production.txt \
 && curl -o /usr/bin/gosu -fsSL ${GOSU_URL} \
 && chmod +sx /usr/bin/gosu \
 # Strip out extra apache files and stupid centos-logos
 && rm -f /etc/httpd/conf.d/*.conf \
 && rm -rf /usr/share/httpd \
 && rm -rf /usr/share/{anaconda,backgrounds,kde4,plymouth,wallpapers}/* \
 && sed -i 's^User apache^User nobody^g' /etc/httpd/conf/httpd.conf \
 # Patch access logs to show originating IP instead of reverse proxy.
 && sed -i 's!LogFormat "%h!LogFormat "%{X-Forwarded-For}i %h!g' /etc/httpd/conf/httpd.conf \
 && sed -ri \
		-e 's!^(\s*CustomLog)\s+\S+!\1 /proc/self/fd/1!g' \
		-e 's!^(\s*ErrorLog)\s+\S+!\1 /proc/self/fd/2!g' \
		/etc/httpd/conf/httpd.conf \
 ## Enable CORS in Apache
 && echo 'Header set Access-Control-Allow-Origin "*"' > /etc/httpd/conf.d/cors.conf \
 && yum -y history undo last \
 && rm -rf /var/cache/yum ~/.cache/pip

# install the source code and config files
COPY dockerfiles/framework/scale/entryPoint.sh /opt/scale/
COPY dockerfiles/framework/scale/*.py /opt/scale/
COPY dockerfiles/framework/scale/app-templates/* /opt/scale/app-templates/
COPY dockerfiles/framework/scale/scale.conf /etc/httpd/conf.d/scale.conf
COPY scale/scale/local_settings_docker.py /opt/scale/scale/local_settings.py
COPY scale /opt/scale
COPY dockerfiles/framework/scale/country_data.json.bz2 /opt/scale/

# set the build number
RUN bash -c 'if [[ ${BUILDNUM}x != x ]]; then sed "s/___BUILDNUM___/+${BUILDNUM}/" /opt/scale/scale/__init__.py.template > /opt/scale/scale/__init__.py; fi'

# install build requirements, build the ui and docs, then remove the extras
COPY scale/pip/docs.txt /tmp/

## By default build the docs
ARG BUILD_DOCS=1

RUN if [ $BUILD_DOCS -eq 1 ]; then pip install --no-cache-dir -r /tmp/docs.txt; make -C /opt/scale/docs code_docs html; pip uninstall -y -r /tmp/docs.txt; fi

# Copy UI assets
COPY scale-ui /opt/scale/ui

WORKDIR /opt/scale

# setup ownership and permissions. create some needed directories
RUN mkdir -p /var/log/scale /var/lib/scale-metrics /scale/input_data /scale/output_data /scale/workspace_mounts \
 && chown -R nobody:nobody /opt/scale /var/log/scale /var/lib/scale-metrics /scale /var/run/httpd \
 && chmod 777 /scale/output_data \
 && chmod a+x entryPoint.sh

USER nobody

# finish the build
RUN python manage.py collectstatic --noinput --settings=

ENTRYPOINT ["./entryPoint.sh"]
