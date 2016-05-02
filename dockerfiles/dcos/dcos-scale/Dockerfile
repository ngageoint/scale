FROM geoint/scale
MAINTAINER Daniel E. Roessner <droessne@ball.com>

VOLUME /opt/scale/static
VOLUME /opt/scale/docs
VOLUME /opt/scale/ui

EXPOSE 8000
EXPOSE 80
EXPOSE 5051

USER root

RUN yum -y install httpd
RUN rm -rf /etc/httpd/conf.d/welcome.conf
COPY scale.conf /etc/httpd/conf.d/scale.conf
COPY local_settings.py /opt/scale/scale/local_settings.py
ADD mesos-0.25.0-py2.7-linux-x86_64.egg /tmp/

RUN easy_install /tmp/mesos-0.25.0-py2.7-linux-x86_64.egg

ENTRYPOINT []

ENV SCALE_DB_NAME='scale' \
    SCALE_DB_USER='scale' \
    SCALE_DB_PASS='scale' \
    SCALE_DB_HOST='scale-db.marathon.slave.mesos' \
    SCALE_DB_PORT='5432' \
    MESOS_MASTER='zk://master.mesos:2181/mesos' \
    DCOS_PACKAGE_FRAMEWORK_NAME='Scale' \
    SCALE_SECRET_KEY='15tryuv4t3hugbv7890aQ' \
    SCALE_USE_X_FORWARDED_HOST='True' \
    SCALE_ALLOWED_HOSTS='*' \
    SCALE_TIME_ZONE='UTC' \
    SCALE_POSTGIS_TEMPLATE='template_postgis' \
    SCALE_NODE_WORK_DIR='/scale_data' \
    DEPLOY_DB='true' \
    SCALE_METRICS_DIR='/tmp' \
    NFS_POSTGRES_UID='26' \
    NFS_POSTGRES_GID='26' \
    DB_DOCKER_IMAGE='docker.io/droessne/dcos-scale-db' \
    SCALE_DB_HOST_VOL=''

ADD startup.sh /opt/scale/startup.sh
RUN chmod +x /opt/scale/startup.sh

ADD scaleConfig.local.js /opt/scale/ui/scripts/scaleConfig.local.js
RUN echo '<html><head><META http-equiv="refresh" content=".5;URL=/scale/"></head></html>' > /var/www/html/index.html

RUN pip install requests
ADD deployDB.py /opt/scale/deployDB.py
RUN chmod +x /opt/scale/deployDB.py

CMD ./startup.sh

#CMD ./manage.py migrate \
# && ./manage.py collectstatic --noinput \
# && ./manage.py load_all_data \
# && ./manage.py scale_scheduler --help \
# && /usr/sbin/httpd \
# && /usr/bin/gunicorn -b 0.0.0.0:8000 -w 4 scale.wsgi:application \
# && sleep 1000 
