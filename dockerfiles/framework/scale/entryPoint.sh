#!/bin/sh

set -e

check_db () {
    if [[ "${DATABASE_URL}x" == "x" ]]
    then
        echo "DATABASE_URL is not populated. Scale requires a valid database url configured defined in dj-database-url format."
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

check_messaging () {
    if [[ "${SCALE_BROKER_URL}x" == "x" ]]
    then
        echo SCALE_BROKER_URL is not populated. Scale requires a valid broker URL configured.
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

    if [[ "${DATABASE_URL}x" == "x" || "${SCALE_LOGGING_ADDRESS}x" == "x" || ${DEPLOY_WEBSERVER} == 'true' ]]
    then
      python -u bootstrap.py | tee bootstrap.log
    fi

    if [[ "${DATABASE_URL}x" == "x" ]]
    then
        export DATABASE_URL=`cat bootstrap.log | grep DATABASE_URL | cut -d '=' -f2`
        export PG_PASS=`cat bootstrap.log | grep PG_PASS | cut -d '=' -f2`
    fi
    echo "${PG_PASS}" >> ~/.pgpass
    chmod 0600 ~/.pgpass

    if [[ "${SCALE_LOGGING_ADDRESS}x" == "x" ]]
    then
        export SCALE_LOGGING_ADDRESS=`cat bootstrap.log | grep LOGGING_ADDRESS | cut -d '=' -f2`
        export SCALE_LOGGING_HEALTH_ADDRESS=`cat bootstrap.log | grep LOGGING_HEALTH_ADDRESS | cut -d '=' -f2`
        export SCALE_ELASTICSEARCH_URLS=`cat bootstrap.log | grep ELASTICSEARCH_URLS | cut -d '=' -f2`
    fi

    if [[ "${SCALE_BROKER_URL}x" == "x" ]]
    then
        export SCALE_BROKER_URL=`cat bootstrap.log | grep BROKER_URL | cut -d '=' -f2`
    fi

    export SCALE_WEBSERVER_ADDRESS=`cat bootstrap.log | grep WEBSERVER_ADDRESS | cut -d '=' -f2`

    # Validate dependencies for bootstrap
    check_db
    check_elastic
    check_logging
    check_messaging

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

# If ENABLE_WEBSERVER is set, we are running the container in web server mode.
if [[ "${ENABLE_WEBSERVER}" == "true" ]]
then
    # Validate dependencies for web server
    check_db
    check_elastic

    exec gosu root /usr/sbin/httpd -D FOREGROUND
fi

# Default fallback entry point that is used by scheduler and pre/post task.
# Appropriate Django command will be specified as arguments
exec python manage.py $*
