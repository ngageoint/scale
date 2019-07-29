# Settings file for use with travis-ci

# Include all the default settings.
from settings import *

# Use the following lines to enable developer/debug mode.
DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

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

DATABASES = {'default': dj_database_url.config(default='postgis://postgres:@localhost:5432/scale')}

# Master settings
MESOS_MASTER = 'zk://localhost:2181/mesos'

# Metrics collection directory
METRICS_DIR = '/tmp'
