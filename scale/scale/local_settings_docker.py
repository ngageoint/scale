# This is the local_settings.py file to be packaged within Scale's Docker image

# Include all the default settings.
from settings import *
import elasticsearch

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SCALE_SECRET_KEY', INSECURE_DEFAULT_KEY)

# Use the following lines to enable developer/debug mode.
DEBUG = bool(os.environ.get('SCALE_DEBUG', False))
TEMPLATE_DEBUG = DEBUG

# Set the external URL context here, default to using SCRIPT_NAME passed by reverse proxy.
FORCE_SCRIPT_NAME = os.environ.get('SCALE_API_URL', None)
USE_X_FORWARDED_HOST = True

ALLOWED_HOSTS = ['*']
override_hosts = os.environ.get('SCALE_ALLOWED_HOSTS')
if override_hosts:
    ALLOWED_HOSTS = override_hosts.split(',')

FRAMEWORK_NAME = os.environ.get('DCOS_PACKAGE_FRAMEWORK_NAME', 'scale')
STATIC_ROOT = os.environ.get('SCALE_STATIC_ROOT', 'static/')
STATIC_URL = os.environ.get('SCALE_STATIC_URL', '/service/%s/static/' % FRAMEWORK_NAME)

LOGGING_ADDRESS = os.environ.get('SCALE_LOGGING_ADDRESS', LOGGING_ADDRESS)
LOGGING_HEALTH_ADDRESS = os.environ.get('SCALE_LOGGING_HEALTH_ADDRESS', LOGGING_HEALTH_ADDRESS)
ELASTICSEARCH_URLS = os.environ.get('SCALE_ELASTICSEARCH_URLS', ELASTICSEARCH_URLS)
if ELASTICSEARCH_URLS:
    ELASTICSEARCH = elasticsearch.Elasticsearch(
        ELASTICSEARCH_URLS.split(','),
        # sniff before doing anything
        sniff_on_start=True,
        # refresh nodes after a node fails to respond
        sniff_on_connection_fail=True,
        # and also every 60 seconds
        sniffer_timeout=60
    )

DB_HOST = os.environ.get('SCALE_DB_HOST', '')
if DB_HOST == '':
        DB_HOST = os.environ.get('DB_PORT_5432_TCP_ADDR', '')
DB_PORT = os.environ.get('SCALE_DB_PORT', '')
if DB_PORT == '':
        DB_PORT = os.environ.get('DB_PORT_5432_TCP_PORT', '5432')

if DB_HOST != '':
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': os.environ.get('SCALE_DB_NAME', 'scale'),
            'USER': os.environ.get('SCALE_DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('SCALE_DB_PASS', 'postgres'),
            'HOST': DB_HOST,
            'PORT': DB_PORT,
        },
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

# Mesos connection information. Default for -m
# This can be something like "127.0.0.1:5050"
# or a zookeeper url like 'zk://host1:port1,host2:port2,.../path`
MESOS_MASTER = os.environ.get('MESOS_MASTER_URL', 'zk://master.mesos:2181/mesos')

# Zookeeper URL for scheduler leader election. If this is None, only a single scheduler is used.
SCHEDULER_ZK = os.environ.get('SCALE_ZK_URL', 'zk://master.mesos:2181/scale')

# The full name for the Scale Docker image (without version tag)
SCALE_DOCKER_IMAGE = os.environ.get('SCALE_DOCKER_IMAGE', SCALE_DOCKER_IMAGE)

# If this container was launched by Marathon parse the version and image from environment
MARATHON_PASSED_IMAGE = os.environ.get('MARATHON_APP_DOCKER_IMAGE', None)
if MARATHON_PASSED_IMAGE:
    if ':' in MARATHON_PASSED_IMAGE:
        DOCKER_VERSION = MARATHON_PASSED_IMAGE.split(':')[-1]
        SCALE_DOCKER_IMAGE = MARATHON_PASSED_IMAGE.replace(':%s' % DOCKER_VERSION, '')
    else:
        DOCKER_VERSION = 'latest'
        SCALE_DOCKER_IMAGE = MARATHON_PASSED_IMAGE


# The location of the config file containing Docker credentials
CONFIG_URI = os.environ.get('CONFIG_URI', CONFIG_URI)

# Logging configuration
LOGGING = LOG_CONSOLE_INFO

