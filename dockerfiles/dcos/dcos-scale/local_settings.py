# Include all the default settings
import os
from settings import *

SECRET_KEY = os.environ.get('SCALE_SECRET_KEY', '15tryuv4t3hugbv7890aQ')

USE_X_FORWARDED_HOST = os.environ.get('SCALE_USE_X_FORWARDED_HOST', 'True')

ALLOWED_HOSTS = [os.environ.get('SCALE_ALLOWED_HOSTS', '*')]

#FORCE_SCRIPT_NAME = os.environ.get('SCALE_FORCE_SCRIPT_NAME', '/api')
#STATIC_URL = os.environ.get('SCALE_STATIC_URL', '/static/')
#STATIC_ROOT = os.environ.get('SCALE_STATIC_ROOT', 'static')
STATIC_ROOT = 'static'
STATIC_URL = '/'+os.environ.get('DCOS_PACKAGE_FRAMEWORK_NAME', '')+'/static/'
FORCE_SCRIPT_NAME = '/'+os.environ.get('DCOS_PACKAGE_FRAMEWORK_NAME', '')+'/api'

TIME_ZONE = os.environ.get('SCALE_TIME_ZONE', 'UTC')

POSTGIS_TEMPLATE = os.environ.get('SCALE_POSTGIS_TEMPLATE', 'template_postgis')

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('SCALE_DB_NAME', ''),
        'USER': os.environ.get('SCALE_DB_USER', ''),
        'PASSWORD': os.environ.get('SCALE_DB_PASS', ''),
        'HOST': os.environ.get('SCALE_DB_HOST', ''),
        'PORT': os.environ.get('SCALE_DB_PORT', '5432'),
    },
}
NODE_WORK_DIR = os.environ.get('SCALE_NODE_WORK_DIR', '/scale_data')

METRICS_DIR = os.environ.get('SCALE_METRICS_DIR', '/tmp')

MESOS_MASTER = os.environ.get('MESOS_MASTER', '')


