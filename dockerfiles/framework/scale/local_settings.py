#@PydevCodeAnalysisIgnore
# Include all the default settings.
from settings import *
import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SCALE_SECRET_KEY']

# Use the following lines to enable developer/debug mode.
DEBUG = os.environ['SCALE_DEBUG', False)
TEMPLATE_DEBUG = DEBUG

# Set the external URL context here
FORCE_SCRIPT_NAME = '/%s/api' % os.environ['SCALE_URL_PREFIX']
USE_X_FORWARDED_HOST = True

ALLOWED_HOSTS = os.environ['SCALE_ALLOWED_HOSTS'].split(',')

STATIC_ROOT = 'static/'
STATIC_URL = '/%s/static/' % os.environ['SCALE_URL_PREFIX']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# Not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'UTC'

# The template database to use when creating your new database.
# By using your own template that already includes the postgis extension,
# you can avoid needing to run the unit tests as a PostgreSQL superuser.
POSTGIS_TEMPLATE = os.environ['SCALE_POSTGIS_TEMPLATE']

# Example settings for using PostgreSQL database with PostGIS.
DB_HOST = os.environ['SCALE_DB_HOST']
if DB_HOST == '':
    DB_HOST = os.environ.get('DB_PORT_5432_TCP_ADDR', 'localhost')
DB_PORT = os.environ['SCALE_DB_PORT']
if DB_PORT == '':
    DB_PORT = os.environ.get('DB_PORT_5432_TCP_PORT', '5432')
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ['SCALE_DB_NAME']
        'USER': os.environ['SCALE_DB_USER_NAME']
        'PASSWORD': os.environ['SCALE_DB_USER_PASSWORD']
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    },
}

# Node settings
NODE_WORK_DIR = os.environ['SCALE_NODE_WORK_DIR']

# If this is true, we don't delete the job_dir after it is finished.
# This might fill up the disk but can be useful for debugging.
SKIP_CLEANUP_JOB_DIR = False

# Master settings
MESOS_MASTER = os.environ['SCALE_MESOS_MASTER']

# Metrics collection directory
METRICS_DIR = os.environ['SCALE_METRICS_DIR']

# Base URL for influxdb access in the form http://<machine>:8086/db/<cadvisor_db_name>/series?u=<username>&p=<password>&
# An invalid or None entry will disable gathering of these statistics
INFLUXDB_BASE_URL = os.environ('SCALE_INFLUXDB_BASE_URL')
if INFLUXDB_BASE_URL == '':
    INFLUXDB_BASE_URL = None
