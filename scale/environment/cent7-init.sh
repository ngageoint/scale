#!/usr/bin/env bash

export SCALE_DB_PORT=55432
export SCALE_DB_PASS=scale-postgres

# Launch a database for Scale testing
systemctl enable docker
systemctl start docker
docker run -d --restart=always -p ${SCALE_DB_PORT}:5432 --name scale-postgis \
    -e POSTGRES_PASSWORD=${SCALE_DB_PASS} mdillon/postgis:9.4-alpine
docker exec -it scale-postgis psql -c "CREATE USER scale PASSWORD 'scale' SUPERUSER;"
docker exec -it scale-postgis psql -c "CREATE DATABASE scale OWNER=scale;"
docker exec -it scale-postgis psql -c  scale -c "CREATE EXTENSION postgis;"

# Install all python dependencies (gotta pin setuptools due to errors during pycparser install)
yum install -y epel-release
yum install -y bzip2 unzip subversion-libs gcc make \
    gdal-python geos libffi-devel openssl-devel postgresql python-virtualenv python-pip python-devel libpqxx-devel

pip install -U virtualenv pip

cp scale/local_settings_dev.py scale/local_settings.py
cat << EOF >> scale/local_settings.py
POSTGIS_TEMPLATE = 'template_postgis'

# Example settings for using PostgreSQL database with PostGIS.
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'scale',
        'USER': 'scale',
        'PASSWORD': 'scale',
        'HOST': 'localhost',
        'PORT': '${SCALE_DB_PORT}',
        'TEST': {'NAME': 'test_scale'},
    },
}
EOF

# Initialize virtual environment
virtualenv environment/scale
environment/scale/bin/pip install -r pip/requirements.txt

# Load up database with schema migrations to date and fixtures
environment/scale/bin/python manage.py migrate
environment/scale/bin/python manage.py load_all_data