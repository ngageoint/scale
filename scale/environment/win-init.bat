set SCALE_DB_PORT=55432
set SCALE_DB_PASS=scale-postgres

REM Launch a database for Scale testing
docker run -d --restart=always -p %SCALE_DB_PORT%:5432 --name scale-postgis -e POSTGRES_PASSWORD=%SCALE_DB_PASS% mdillon/postgis:9.4-alpine

REM Configure database
echo "Giving Postgres a moment to start up before initializing..."
ping 127.0.0.1 -n 6 > nul
echo "CREATE USER scale PASSWORD 'scale' SUPERUSER;" >> database-commands.sql
echo "CREATE DATABASE scale OWNER=scale;" >> database-commands.sql
docker cp database-commands.sql scale-postgis:/database-commands.sql
del database-commands.sql
docker exec -it scale-postgis su postgres -c 'psql -f /database-commands.sql'
docker exec -it scale-postgis su postgres -c 'psql scale -c "CREATE EXTENSION postgis;"'

REM Set default connection string for database
copy scale/local_settings_dev.py scale/local_settings.py
echo "POSTGIS_TEMPLATE = 'template_postgis'" >> scale/local_settings.py
echo >> scale/local_settings.py
echo "DATABASES = {" >> scale/local_settings.py
echo "    'default': {" >> scale/local_settings.py
echo "        'ENGINE': 'django.contrib.gis.db.backends.postgis'," >> scale/local_settings.py
echo "        'NAME': 'scale'," >> scale/local_settings.py
echo "        'USER': 'scale'," >> scale/local_settings.py
echo "        'PASSWORD': 'scale'," >> scale/local_settings.py
echo "        'HOST': 'localhost'," >> scale/local_settings.py
echo "        'PORT': '${SCALE_DB_PORT}'," >> scale/local_settings.py
echo "        'TEST': {'NAME': 'test_scale'}," >> scale/local_settings.py
echo "    }," >> scale/local_settings.py
echo "}" >> scale/local_settings.py

REM Initialize virtual environment
virtualenv environment\scale
environment\scale\bin\pip install -r pip\requirements.txt

REM Load up database with schema migrations to date and fixtures
environment\scale\bin\python manage.py migrate
environment\scale\bin\python manage.py load_all_data