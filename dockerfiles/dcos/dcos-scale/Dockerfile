FROM geoint/scale
MAINTAINER Daniel E. Roessner <droessne@ball.com>

EXPOSE 8000
EXPOSE 80
EXPOSE 5051

USER root

RUN yum -y install httpd
RUN rm -rf /etc/httpd/conf.d/welcome.conf
COPY scale.conf /etc/httpd/conf.d/scale.conf
ADD mesos-0.25.0-py2.7-linux-x86_64.egg /tmp/

RUN easy_install /tmp/mesos-0.25.0-py2.7-linux-x86_64.egg

ENTRYPOINT []

ENV DEPLOY_DB='false' \
    PORT0='' 
#ENV SCALE_DB_NAME='scale' \
#    SCALE_DB_USER='scale' \
#    SCALE_DB_PASS='scale' \
#    SCALE_DB_HOST='scale-db.marathon.slave.mesos' \
#    SCALE_DB_PORT='23777' \
#    MESOS_MASTER_URL='zk://master.mesos:2181/mesos' \
#    DCOS_PACKAGE_FRAMEWORK_NAME='Scale' \
#    SCALE_SECRET_KEY='15tryuv4t3hugbv7890aQ' \
#    SCALE_ALLOWED_HOSTS='*' \
#    SCALE_API_URL='/ui/api' \
#    SCALE_STATIC_URL='/service/Scale/ui/static/' \
#    SCALE_STATIC_ROOT='static/' \
#    SCALE_DOCKER_IMAGE='devdocker-reg:5000/scale' \
#    SCALE_ZK_URL='None' 

ADD startup.sh /opt/scale/startup.sh
RUN chmod +x /opt/scale/startup.sh

RUN echo '<html><head><META http-equiv="refresh" content=".5;URL=./ui/"></head></html>' > /var/www/html/index.html

RUN pip install requests
ADD deployDB.py /opt/scale/deployDB.py
RUN chmod +x /opt/scale/deployDB.py

CMD ./startup.sh
