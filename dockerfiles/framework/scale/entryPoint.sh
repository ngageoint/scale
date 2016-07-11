#!/bin/sh

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

if [[ ${DEPLOY_DB} == 'true' ]]
then
    export SCALE_DB_PORT=$(./deployDb.py)
    echo "DATABASE_PORT: ${SCALE_DB_PORT}"
fi

# wait for postgres database to spin up
CHECK1="0"
CHECK=$(/usr/bin/psql -U ${SCALE_DB_USER} -h ${SCALE_DB_HOST} -w -p ${SCALE_DB_PORT} &> /tmp/check; cat /tmp/check | head -1 | cut -d ':' -f 3)
while [[ "$CHECK1" = "0" ]]; do
  if [[ "$CHECK" = " Connection refused" ]]; then
    sleep 2;
    CHECK=$(/usr/bin/psql -U ${SCALE_DB_USER} -h ${SCALE_DB_HOST} -w -p ${SCALE_DB_PORT} &> /tmp/check; cat /tmp/check | head -1 | cut -d ':' -f 3);
    echo ${CHECK};
  elif [[ "$CHECK" = " No route to host" ]]; then
   sleep 2;
    CHECK=$(/usr/bin/psql -U ${SCALE_DB_USER} -h ${SCALE_DB_HOST} -w -p ${SCALE_DB_PORT} &> /tmp/check; cat /tmp/check | head -1 | cut -d ':' -f 3);
    echo ${CHECK};
  else
    CHECK1="1"
  fi
done

if [[ ${INIT_DB} == 'true' ]]
then
    /usr/bin/psql -U scale -h ${SCALE_DB_HOST} -w -p ${SCALE_DB_PORT} -c "CREATE EXTENSION postgis;"
    ./manage.py migrate
    ./manage.py load_all_data
fi

if [[ ${ENABLE_HTTPD} == 'true' ]]
then
    gosu root /usr/sbin/httpd
fi

if [[ ${ENABLE_NFS} == 'true' ]]
then
   gosu root /usr/sbin/rpcbind
   gosu root /usr/sbin/rpc.statd
fi

if [[ ${ENABLE_GUNICORN} == 'true' ]]
then
    /usr/bin/gunicorn -D -b 0.0.0.0:8000 -w 4 scale.wsgi:application
fi

exec ./manage.py $*
