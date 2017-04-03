#!/usr/bin/env bash

# Clean up old Postgres and install 9.4 version
service postgresql stop
apt-get --purge remove -y postgresql\*
su -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ trusty-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
apt-get update
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
apt-get install -y --force-yes  postgresql-9.4 postgresql-contrib-9.4 postgresql-9.4-postgis-2.3
sed 's^local   all             all                                     peer^local   all             all                                     trust^g' -i /etc/postgresql/9.4/main/pg_hba.conf
service postgresql start

# Install all python dependencies (gotta pin setuptools due to errors during pycparser install)
sudo apt-get install build-essential libssl-dev libffi-dev python-dev
sudo pip install -U pip
sudo pip install setuptools==33.1.1
sudo pip install -r pip/requirements.txt

cat << EOF > database-commands.sql
CREATE USER scale PASSWORD 'scale' SUPERUSER;
CREATE DATABASE scale OWNER=scale;
EOF
sudo su postgres -c "psql -f database-commands.sql"
rm database-commands.sql
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