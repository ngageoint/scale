#!/usr/bin/env bash

export SCALE_DB_PORT=55432
export SCALE_MESSAGE_PORT=55672
export SCALE_DB_PASS=scale-postgres

# Configure docker to always run
chkconfig docker on
service docker start

# Ensure no previous containers or configuration exist
docker stop scale-postgis scale-rabbitmq
docker rm scale-postgis scale-rabbitmq
rm -fr environment/scale

# Launch a database for Scale testing
docker run -d --restart=always -p ${SCALE_DB_PORT}:5432 --name scale-postgis \
    -e POSTGRES_PASSWORD=${SCALE_DB_PASS} mdillon/postgis:9.4-alpine
echo Giving Postgres a moment to start up before initializing...
sleep 10

docker run -d --restart=always -p ${SCALE_MESSAGE_PORT}:5672 --name scale-rabbitmq \
    rabbitmq:3.6-management

# Configure database
cat << EOF > database-commands.sql
CREATE USER scale PASSWORD 'scale' SUPERUSER;
CREATE DATABASE scale OWNER=scale;
EOF
docker cp database-commands.sql scale-postgis:/database-commands.sql
rm database-commands.sql
docker exec -it scale-postgis su postgres -c 'psql -f /database-commands.sql'
docker exec -it scale-postgis su postgres -c 'psql scale -c "CREATE EXTENSION postgis;"'

# Install all python dependencies (gotta pin setuptools due to errors during pycparser install)
yum install -y bzip2 unzip subversion-libs gcc make \
    gdal-python geos libffi-devel openssl-devel postgresql libpqxx-devel

cp scale/local_settings_dev.py scale/local_settings.py
cat << EOF >> scale/local_settings.py
BROKER_URL = 'amqp://guest:guest@localhost:${SCALE_MESSAGE_PORT}//'

POSTGIS_TEMPLATE = 'template_postgis'

DATABASES = {'default': dj_database_url.config(default='postgis://scale:scale@localhost:${SCALE_DB_PORT}/scale')}
EOF

# Initialize virtual environment
virtualenv environment/scale
environment/scale/bin/pip install -r pip/requirements.txt

# Load up database with schema migrations to date and fixtures
environment/scale/bin/python manage.py migrate
environment/scale/bin/python manage.py load_all_data

# Clean up logs to eliminate permission issues
rm -fr ../scale/logs
