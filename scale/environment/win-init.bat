set SCALE_DB_PORT=55432
set SCALE_MESSAGE_PORT=55672
set SCALE_DB_PASS=scale-postgres

REM Launch a database for Scale testing
docker run -d --restart=always -p %SCALE_DB_PORT%:5432 --name scale-postgis -e POSTGRES_PASSWORD=%SCALE_DB_PASS% mdillon/postgis:9.4-alpine

REM Launch a message broker for Scale testing
docker run -d --restart=always -p %SCALE_MESSAGE_PORT%:5672 --name scale-rabbitmq rabbitmq:3.6-management

REM Configure database
echo "Giving Postgres a moment to start up before initializing..."
ping 127.0.0.1 -n 6 > nul
echo CREATE USER scale PASSWORD 'scale' SUPERUSER; >> database-commands.sql
echo CREATE DATABASE scale OWNER=scale; >> database-commands.sql
docker cp database-commands.sql scale-postgis:/database-commands.sql
del database-commands.sql
docker exec -it scale-postgis psql -U postgres -f /database-commands.sql
docker exec -it scale-postgis psql -U scale -c "CREATE EXTENSION postgis;" scale

copy scale\local_settings_dev.py scale\local_settings.py
REM Set default connection string for database
echo BROKER_URL = 'amqp://guest:guest@localhost:%SCALE_MESSAGE_PORT%//' >> scale\local_settings.py
echo POSTGIS_TEMPLATE = 'template_postgis' >> scale\local_settings.py
echo. >> scale\local_settings.py
echo DATABASES = {'default': dj_database_url.config(default='postgis://scale:scale@localhost:%SCALE_DB_PORT%/scale')} >> scale\local_settings.py

REM Initialize virtual environment
virtualenv environment\scale
environment\scale\Scripts\pip.exe install -r pip\requirements.txt

REM Load up database with schema migrations to date and fixtures
environment\scale\Scripts\python.exe manage.py migrate
environment\scale\Scripts\python.exe manage.py load_all_data