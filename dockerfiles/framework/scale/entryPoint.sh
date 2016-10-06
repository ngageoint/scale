#!/bin/sh -x

if [[ ${DCOS_URL}x != x ]]
then
 dcos config set core.dcos_url $DCOS_URL
else
 dcos config set core.dcos_url http://master.mesos
fi

if [[ ${DEPLOY_DB} == 'true' ]] || [[ ${DEPLOY_LOGGING} == 'true' ]]
then
  ./dcos_cli.py > dcos_cli.log
fi

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

if [[ ${DEPLOY_DB} == 'true' ]]
then
    export SCALE_DB_PORT=`cat dcos_cli.log | grep DB_PORT | cut -d '=' -f2`
    echo "DATABASE_PORT: ${SCALE_DB_PORT}"
fi
echo "${SCALE_DB_HOST}:${SCALE_DB_PORT}:*:${SCALE_DB_USER}:${SCALE_DB_PASS}" >> ~/.pgpass
chmod 0600 ~/.pgpass

if [[ ${DEPLOY_LOGGING} == 'true' ]]
then
    export SCALE_LOGGING_ADDRESS=`cat dcos_cli.log | grep LOGGING_ADDRESS | cut -d '=' -f2`
    export SCALE_ELASTICSEARCH_URL=`cat dcos_cli.log | grep ELASTICSEARCH_URL | cut -d '=' -f2`
    echo "LOGGING ADDRESS: ${SCALE_LOGGING_ADDRESS}"
    echo "ELASTICSEARCH URL: ${SCALE_ELASTICSEARCH_URL}"
fi

if [[ ${INIT_DB} == 'true' ]]
then
    /usr/bin/psql -U scale -h ${SCALE_DB_HOST} -w -p ${SCALE_DB_PORT} -c "CREATE EXTENSION postgis;"
    ./manage.py migrate
    ./manage.py load_all_data
fi
if [[ ${LOAD_COUNTRY_DATA} == 'true' ]]
then
    bunzip2 country_data.json.bz2
    ./manage.py loaddata country_data.json
fi

if [[ ${ENABLE_HTTPD} == 'true' ]]
then
    gosu root sed -i 's^User apache^User scale^g' /etc/httpd/conf/httpd.conf
    gosu root /usr/sbin/httpd
fi

if [[ ${ENABLE_GUNICORN} == 'true' ]]
then
    /usr/bin/gunicorn -D -b 0.0.0.0:8000 -w 4 scale.wsgi:application
fi

exec ./manage.py $*
