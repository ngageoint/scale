#@PydevCodeAnalysisIgnore

# This is a sample file that can be used as a starting place for creating a
# local_settings.py file for production purposes. Copy this file and rename it
# to local_settings.py. Then make any additional changes you need to configure
# it for your production environment.

# Include all the default settings.
from settings import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

# Use the following lines to enable developer/debug mode.
DEBUG = False
TEMPLATE_DEBUG = DEBUG

# Set the external URL context here
FORCE_SCRIPT_NAME = '/scale3/api'
USE_X_FORWARDED_HOST = True

ALLOWED_HOSTS = []

STATIC_ROOT = 'static/'
STATIC_URL = '/scale/static/'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# Not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'UTC'

# The template database to use when creating your new database.
# By using your own template that already includes the postgis extension,
# you can avoid needing to run the unit tests as a PostgreSQL superuser.
POSTGIS_TEMPLATE = 'template1'

# Example settings for using PostgreSQL database with PostGIS.
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'scale',
        'USER': 'USER_NAME',
        'PASSWORD': 'USER_PASSWORD',
        'HOST': 'DATABASE_HOST',
        'PORT': '5432',
    },
}

# Node settings
NODE_WORK_DIR = '/tmp/scale/work'

# If this is true, we don't delete the job_dir after it is finished.
# This might fill up the disk but can be useful for debugging.
SKIP_CLEANUP_JOB_DIR = False

# Master settings
MESOS_MASTER = ''

# Metrics collection directory
#METRICS_DIR = ''

# Base URL for influxdb access in the form http://<machine>:8086/db/<cadvisor_db_name>/series?u=<username>&p=<password>&
# An invalid or None entry will disable gathering of these statistics
#INFLUXDB_BASE_URL = None
