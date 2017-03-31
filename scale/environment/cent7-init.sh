#!/usr/bin/env bash

export SCALE_DB_HOST=localhost
export SCALE_DB_PORT=55432
export SCALE_DB_USER=postgres
export SCALE_DB_PASS=scale-postgres

# Launch a database for Scale testing
systemctl enable docker
systemctl start docker
docker run -d --restart=always -p ${SCALE_DB_PORT}:5432 --name scale-postgis \
    -e POSTGRES_PASSWORD=${SCALE_DB_PASS} mdillon/postgis:9.4-alpine

# Install all python dependencies (gotta pin setuptools due to errors during pycparser install)
yum install -y epel-release
yum install -y bzip2 unzip subversion-libs gcc make \
    gdal-python geos libffi-devel openssl-devel postgresql protobuf python-virtualenv python-pip python-devel

pip install -U virtualenv pip

cat << EOF > database-commands.sql
CREATE USER scale PASSWORD 'scale' SUPERUSER;
CREATE DATABASE scale OWNER=scale;
EOF

# Create pgpass file for authentication to postgres user and initialize scale DB within Docker
echo "${SCALE_DB_HOST}:${SCALE_DB_PORT}:*:${SCALE_DB_USER}:${SCALE_DB_PASS}" >> ~/.pgpass
echo "${SCALE_DB_HOST}:${SCALE_DB_PORT}:*:scale:scale" >> ~/.pgpass
chmod 0600 ~/.pgpass

psql -U ${SCALE_DB_USER} -h ${SCALE_DB_HOST} -w -p ${SCALE_DB_PORT} -f database-commands.sql
psql -U scale -h ${SCALE_DB_HOST} -w -p ${SCALE_DB_PORT} scale -c "CREATE EXTENSION postgis;"

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