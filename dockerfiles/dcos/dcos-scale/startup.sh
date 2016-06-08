#!/bin/bash
sed -i "s/framework.name\ =\ 'Scale'/framework.name\ =\ '"$DCOS_PACKAGE_FRAMEWORK_NAME"'/" /opt/scale/scheduler/management/commands/scale_scheduler.py
sed -i "/framework.name/ a\ \ \ \ \ \ \ \ framework.webui_url = 'http://"$DCOS_PACKAGE_FRAMEWORK_NAME".marathon.slave.mesos:"$PORT0"/'" scheduler/management/commands/scale_scheduler.py
sed -i 's/\/SCALE/\/'$DCOS_PACKAGE_FRAMEWORK_NAME'/' /etc/httpd/conf.d/scale.conf
sed -i 's/\/api/.\/api/' /opt/scale/ui/config/scaleConfig.json
sed -i 's/\/docs/.\/docs/' /opt/scale/ui/config/scaleConfig.json

if [[ "$PORT0" != "" ]]; then
  sed -i '/Listen 80/ aListen '$PORT0 /etc/httpd/conf/httpd.conf
fi

if [[ "$DEPLOY_DB" = "true" ]]; then
  chmod +x ./deployDB.py
  export SCALE_DB_PORT=`./deployDB.py`
  echo 'DATABASE_PORT: '$SCALE_DB_PORT
fi

CHECK1="0"
CHECK=`/usr/bin/psql -U scale -h $SCALE_DB_HOST -w -p $SCALE_DB_PORT &> /tmp/check; cat /tmp/check | head -1 | cut -d ':' -f 3`
while [[ "$CHECK1" = "0" ]]; do
  if [[ "$CHECK" = " Connection refused" ]]; then
    sleep 2;
    CHECK=`/usr/bin/psql -U scale -h $SCALE_DB_HOST -w -p $SCALE_DB_PORT &> /tmp/check; cat /tmp/check | head -1 | cut -d ':' -f 3`;
    echo $CHECK;
  elif [[ "$CHECK" = " No route to host" ]]; then
   sleep 2;
    CHECK=`/usr/bin/psql -U scale -h $SCALE_DB_HOST -w -p $SCALE_DB_PORT &> /tmp/check; cat /tmp/check | head -1 | cut -d ':' -f 3`;
    echo $CHECK;
  else
    CHECK1="1"
  fi
done

./manage.py makemigrations
./manage.py migrate
./manage.py collectstatic --noinput
./manage.py load_all_data
/usr/sbin/httpd
/usr/bin/gunicorn -b 0.0.0.0:8000 -w 4 scale.wsgi:application &
./manage.py scale_scheduler
