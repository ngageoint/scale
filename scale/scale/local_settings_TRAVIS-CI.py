#@PydevCodeAnalysisIgnore

# Settings file for use with travis-ci

# Include all the default settings.
from settings import *

# Use the following lines to enable developer/debug mode.
DEBUG = False
TEMPLATE_DEBUG = DEBUG

# Set the external URL context here
FORCE_SCRIPT_NAME = '/'
USE_X_FORWARDED_HOST = True

ALLOWED_HOSTS = ["*"]

STATIC_ROOT = 'static'
STATIC_URL = '/static/'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# Not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'UTC'

SECRET_KEY = "0fnk28edjh"

# The template database to use when creating your new database.
# By using your own template that already includes the postgis extension,
# you can avoid needing to run the unit tests as a PostgreSQL superuser.
#POSTGIS_TEMPLATE = 'scale'

DATABASES = {
   'default': {
      'ENGINE': 'django.contrib.gis.db.backends.postgis',
      'NAME': 'scale',
      'USER': 'postgres',
      'PASSWORD': '',
      'HOST': 'localhost',
   },
}

# Node settings
NODE_WORK_DIR = '/scale_data'

# If this is true, we don't delete the job_dir after it is finished.
# This might fill up the disk but can be useful for debugging.
SKIP_CLEANUP_JOB_DIR = False

# Master settings
MESOS_MASTER = 'zk://localhost:2181/mesos'

# Metrics collection directory
METRICS_DIR = '/tmp'

# Base URL for influxdb access in the form http://<machine>:8086/db/<cadvisor_db_name>/series?u=<username>&p=<password>&
# An invalid or None entry will disable gathering of these statistics
#INFLUXDB_BASE_URL = None
