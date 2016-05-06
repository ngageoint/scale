# This is the local_settings.py file to be packaged within Scale's Docker image

# Include all the default settings.
from settings import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SCALE_SECRET_KEY', INSECURE_DEFAULT_KEY)

# Use the following lines to enable developer/debug mode.
DEBUG = bool(os.environ.get('SCALE_DEBUG', False))
TEMPLATE_DEBUG = DEBUG

# Set the external URL context here
FORCE_SCRIPT_NAME = os.environ.get('SCALE_API_URL', '/scale/api')
USE_X_FORWARDED_HOST = True

ALLOWED_HOSTS = [os.environ.get('SCALE_ALLOWED_HOSTS', '*')]

STATIC_ROOT = os.environ.get('SCALE_STATIC_ROOT', 'static/')
STATIC_URL = os.environ.get('SCALE_STATIC_URL', '/scale/static/')

DEFAULT_SCHEDULER_DOCKER_REPOSITORY = os.environ.get('SCALE_DEFAULT_SCHEDULER_DOCKER_REPOSITORY', DEFAULT_SCHEDULER_DOCKER_REPOSITORY)

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

# Mesos connection information. Default for -m
# This can be something like "127.0.0.1:5050"
# or a zookeeper url like 'zk://host1:port1,host2:port2,.../path`
MESOS_MASTER = os.environ.get('MESOS_MASTER_URL', None)

# Zookeeper URL for scheduler leader election. If this is None, only a single scheduler is used.
SCHEDULER_ZK = os.environ.get('SCALE_ZK_URL', None)
