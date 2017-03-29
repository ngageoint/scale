#!/usr/bin/env bash

# Clean up old Postgres and install 9.4 version
docker run -d --restart=always -p 55432:5432 --name scale-postgis -e POSTGRES_PASSWORD=scale-postgres mdillon/postgis:9.4-alpine

# Install all python dependencies (gotta pin setuptools due to errors during pycparser install)
sudo apt-get install build-essential libssl-dev libffi-dev python-dev
sudo pip install -U pip
sudo pip install setuptools==33.1.1
sudo pip install -r pip/build_linux.txt

cat << EOF > database-commands.sql
CREATE USER scale PASSWORD 'scale' SUPERUSER;
CREATE DATABASE scale OWNER=scale;
EOF
sudo su postgres -c "psql -f database-commands.sql"
sudo su postgres -c "psql scale -c 'CREATE EXTENSION postgis'"

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
        'PORT': '5432',
        'TEST': {'NAME': 'test_scale'},
    },
}
EOF

# Load up database with schema migrations to date and fixtures
python manage.py migrate
python manage.py load_all_data