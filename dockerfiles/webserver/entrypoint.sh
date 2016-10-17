#!/usr/bin/env sh

if [[ ${DCOS_PACKAGE_FRAMEWORK_NAME}x != x ]]
then
    sed -i "s/framework.name\ =\ 'Scale'/framework.name\ =\ '"${DCOS_PACKAGE_FRAMEWORK_NAME}"'/" /opt/scale/scheduler/management/commands/scale_scheduler.py
    sed -i "/framework.name/ a\ \ \ \ \ \ \ \ framework.webui_url = 'http://"${DCOS_PACKAGE_FRAMEWORK_NAME}".marathon.slave.mesos:"${PORT0}"/'" scheduler/management/commands/scale_scheduler.py
    gosu root sed -i 's/\/SCALE/\/'${DCOS_PACKAGE_FRAMEWORK_NAME}'/' /etc/httpd/conf.d/scale.conf
    sed -i 's/\/api/.\/api/' /opt/scale/ui/config/scaleConfig.json
    sed -i 's/\/docs/.\/docs/' /opt/scale/ui/config/scaleConfig.json
    gosu root sed -i 's/PREFIX//' /etc/httpd/conf.d/scale.conf
fi

if [[ ${PORT0}x != x ]]
then
  gosu root sed -i '/Listen 80/ aListen '${PORT0} /etc/httpd/conf/httpd.conf
fi

echo "${SCALE_DB_HOST}:${SCALE_DB_PORT}:*:${SCALE_DB_USER}:${SCALE_DB_PASS}" >> ~/.pgpass
chmod 0600 ~/.pgpass

if [[ ${ENABLE_HTTPD} == 'true' ]]
then
    gosu root sed -i 's^User apache^User scale^g' /etc/httpd/conf/httpd.conf
    gosu root /usr/sbin/httpd
fi

exec /usr/bin/gunicorn -c gunicorn.conf.py scale.wsgi:application

