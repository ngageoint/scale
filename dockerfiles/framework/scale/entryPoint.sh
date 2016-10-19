#!/bin/sh -x

if [[ ${DCOS_URL}x != x ]]
then
 dcos config set core.dcos_url $DCOS_URL
else
 dcos config set core.dcos_url http://master.mesos
fi

# TODO: Replace this with a pinned value if we care about key change across container restart
export SCALE_SECRET_KEY=`python -c "import random;import string;print(''.join(random.SystemRandom().choice(string.hexdigits) for _ in range(50)))"`
echo "SCALE_SECRET_KEY: ${SCALE_SECRET_KEY}"

if [[ ${DEPLOY_DB} == 'true' ]] || [[ ${DEPLOY_LOGGING} == 'true' || ${DEPLOY_WEBSERVER} == 'true' ]]
then
  python dcos_cli.py > dcos_cli.log
fi

if [[ ${DEPLOY_DB} == 'true' ]]
then
    export SCALE_DB_PORT=`cat dcos_cli.log | grep DB_PORT | cut -d '=' -f2`
    export SCALE_DB_HOST=`cat dcos_cli.log | grep DB_HOST | cut -d '=' -f2`
    echo "DATABASE_HOST: ${SCALE_DB_HOST}"
    echo "DATABASE_PORT: ${SCALE_DB_PORT}"
fi
echo "${SCALE_DB_HOST}:${SCALE_DB_PORT}:*:${SCALE_DB_USER}:${SCALE_DB_PASS}" >> ~/.pgpass
chmod 0600 ~/.pgpass

if [[ ${DEPLOY_LOGGING} == 'true' ]]
then
    export SCALE_LOGGING_ADDRESS=`cat dcos_cli.log | grep LOGGING_ADDRESS | cut -d '=' -f2`
    export SCALE_ELASTICSEARCH_URLS=`cat dcos_cli.log | grep ELASTICSEARCH_URLS | cut -d '=' -f2`
    echo "LOGGING ADDRESS: ${SCALE_LOGGING_ADDRESS}"
    echo "ELASTICSEARCH URLS: ${SCALE_ELASTICSEARCH_URLS}"
fi

if [[ ${INIT_DB} == 'true' ]]
then
    /usr/bin/psql -U scale -h ${SCALE_DB_HOST} -w -p ${SCALE_DB_PORT} -c "CREATE EXTENSION postgis;"
    python manage.py migrate
    python manage.py load_all_data
fi
if [[ ${LOAD_COUNTRY_DATA} == 'true' ]]
then
    bunzip2 country_data.json.bz2
    python manage.py loaddata country_data.json
fi

if [[ ${DCOS_PACKAGE_FRAMEWORK_NAME}x != x ]]
then
    sed -i "s/framework.name\ =\ 'Scale'/framework.name\ =\ '"${DCOS_PACKAGE_FRAMEWORK_NAME}"'/" /opt/scale/scheduler/management/commands/scale_scheduler.py
    sed -i "/framework.name/ a\ \ \ \ \ \ \ \ framework.webui_url = 'http://"${DCOS_PACKAGE_FRAMEWORK_NAME}".marathon.slave.mesos:"${PORT0}"/'" scheduler/management/commands/scale_scheduler.py
    sed -i 's^/api^./api^' /opt/scale/ui/config/scaleConfig.json
    sed -i 's^/docs^./docs^' /opt/scale/ui/config/scaleConfig.json
fi

# If ENABLE_WEBSERVER is set, we are running the container in webserver mode.
# If this is false we are either launching a pre/post task or the scheduler.
if [[ ${ENABLE_WEBSERVER} == 'true' ]]
then
    gosu root sed -i 's^User apache^User scale^g' /etc/httpd/conf/httpd.conf
    gosu root sed -i 's/\/SCALE/\/'${DCOS_PACKAGE_FRAMEWORK_NAME}'/' /etc/httpd/conf.d/scale.conf
    gosu root /usr/sbin/httpd

    exec /usr/bin/gunicorn -c gunicorn.conf.py scale.wsgi:application
else
    exec python manage.py $*
fi
