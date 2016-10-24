#!/bin/sh

set -e

check_db () {
    if [[ "${SCALE_DB_HOST}x" == "x" ]]
    then
        echo SCALE_DB_HOST is not populated. Scale requires a valid database host configured.
        exit 1
    fi
}

check_logging () {
    if [[ "${SCALE_LOGGING_ADDRESS}x" == "x" ]]
    then
        echo SCALE_LOGGING_ADDRESS is not populated. Scale requires a valid logstash URL configured.
        exit 1
    fi
}

check_elastic () {
    if [[ "${SCALE_ELASTICSEARCH_URLS}x" == "x" ]]
    then
        echo SCALE_ELASTICSEARCH_URLS is not populated. Scale requires a valid list of Elasticsearch URLs configured.
        exit 1
    fi
}

# If ENABLE_BOOTSTRAP is set, we are bootstrapping other components in a DCOS package configuration
if [[ "${ENABLE_BOOTSTRAP}" == "true" ]]
then
    if [[ "${SCALE_SECRET_KEY}x" == "x" ]]
    then
      export SCALE_SECRET_KEY=`python -c "import random;import string;print(''.join(random.SystemRandom().choice(string.hexdigits) for _ in range(50)))"`
    fi

    if [[ "${SCALE_DB_HOST}x" == "x" || "${SCALE_LOGGING_ADDRESS}x" == "x" || ${DEPLOY_WEBSERVER} == 'true' ]]
    then
      python -u bootstrap.py | tee bootstrap.log
    fi

    if [[ "${SCALE_DB_HOST}x" == "x" ]]
    then
        export SCALE_DB_PORT=`cat bootstrap.log | grep DB_PORT | cut -d '=' -f2`
        export SCALE_DB_HOST=`cat bootstrap.log | grep DB_HOST | cut -d '=' -f2`
    fi
    echo "${SCALE_DB_HOST}:${SCALE_DB_PORT}:*:${SCALE_DB_USER}:${SCALE_DB_PASS}" >> ~/.pgpass
    chmod 0600 ~/.pgpass

    if [[ "${SCALE_LOGGING_ADDRESS}x" == "x" ]]
    then
        export SCALE_LOGGING_ADDRESS=`cat bootstrap.log | grep LOGGING_ADDRESS | cut -d '=' -f2`
        export SCALE_ELASTICSEARCH_URLS=`cat bootstrap.log | grep ELASTICSEARCH_URLS | cut -d '=' -f2`
    fi

    # Validate dependencies for bootstrap
    check_db
    check_elastic
    check_logging

    # Initialize schema and initial data
    # psql command or'ed with true so that pre-existing postgis won't cause script to terminate
    /usr/bin/psql -U scale -h ${SCALE_DB_HOST} -w -p ${SCALE_DB_PORT} -c "CREATE EXTENSION postgis;" || true
    python manage.py migrate
    python manage.py load_all_data
    # Load country boundary data
    # bunzip2 command or'ed with true so that link errors won't cause script to terminate
    bunzip2 country_data.json.bz2 || true
    python manage.py loaddata country_data.json
fi

if [[ "${DCOS_PACKAGE_FRAMEWORK_NAME}x" != "x"  && "${ENABLE_WEBSERVER}" != "true" ]]
then
    sed -i "s/framework.name\ =\ 'Scale'/framework.name\ =\ '"${DCOS_PACKAGE_FRAMEWORK_NAME}"'/" /opt/scale/scheduler/management/commands/scale_scheduler.py
    sed -i "/framework.name/ a\ \ \ \ \ \ \ \ framework.webui_url = 'http://"${DCOS_PACKAGE_FRAMEWORK_NAME}".marathon.slave.mesos:"${PORT0}"/'" scheduler/management/commands/scale_scheduler.py
fi

# If ENABLE_WEBSERVER is set, we are running the container in web server mode.
if [[ "${ENABLE_WEBSERVER}" == "true" ]]
then
    # Validate dependencies for web server
    check_db
    check_elastic

    gosu root sed -i 's^User apache^User scale^g' /etc/httpd/conf/httpd.conf
    gosu root sed -i 's/\/SCALE/\/'${DCOS_PACKAGE_FRAMEWORK_NAME}'/' /etc/httpd/conf.d/scale.conf
    sed -i 's^/api^./api^' /opt/scale/ui/config/scaleConfig.json
    sed -i 's^/docs^./docs^' /opt/scale/ui/config/scaleConfig.json
    gosu root /usr/sbin/httpd

    exec /usr/bin/gunicorn -c gunicorn.conf.py scale.wsgi:application
fi

# Default fallback entrypoint that is used by scheduler and pre/post task.
# Appropriate Django command will be specified as arguments
exec python manage.py $*
