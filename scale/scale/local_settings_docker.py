# This is the local_settings.py file to be packaged within Scale's Docker image

# Include all the default settings.
from settings import *
import elasticsearch

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SCALE_SECRET_KEY', INSECURE_DEFAULT_KEY)

# Use the following lines to enable developer/debug mode.
DEBUG = get_env_boolean('DJANGO_DEBUG')
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

# Set the external URL context here, default to using SCRIPT_NAME passed by reverse proxy.
FORCE_SCRIPT_NAME = os.environ.get('SCALE_API_URL', None)
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Ensure backend uses HTTPS for auth callbacks
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

ALLOWED_HOSTS = ['*']
override_hosts = os.environ.get('SCALE_ALLOWED_HOSTS')
if override_hosts:
    ALLOWED_HOSTS = override_hosts.split(',')

FRAMEWORK_NAME = os.environ.get('DCOS_PACKAGE_FRAMEWORK_NAME', 'scale')
WEBSERVER_ADDRESS = os.getenv('SCALE_WEBSERVER_ADDRESS')
SERVICE_SECRET = os.getenv('SERVICE_SECRET')
PRINCIPAL = os.getenv('PRINCIPAL')
SECRET = os.getenv('SECRET')

STATIC_ROOT = os.environ.get('SCALE_STATIC_ROOT', 'static/')
STATIC_URL = os.environ.get('SCALE_STATIC_URL', '/service/%s/static/' % FRAMEWORK_NAME)

LOGGING_ADDRESS = os.environ.get('LOGGING_ADDRESS', LOGGING_ADDRESS)
LOGGING_HEALTH_ADDRESS = os.environ.get('LOGGING_HEALTH_ADDRESS', LOGGING_HEALTH_ADDRESS)
if ELASTICSEARCH_URL:
    ELASTICSEARCH = elasticsearch.Elasticsearch(
        [ELASTICSEARCH_URL],
        # disable all sniffing
        sniff_on_start=False,
        # refresh nodes after a node fails to respond
        sniff_on_connection_fail=False,
        # dont verify SSL certificates presently
        verify_certs=False
    )

    ELASTICSEARCH_VERSION = ELASTICSEARCH.info()['version']['number']


# Broker URL for connection to messaging backend. Bootstrap must populate.
BROKER_URL = os.environ.get('SCALE_BROKER_URL', BROKER_URL)
QUEUE_NAME = os.environ.get('SCALE_QUEUE_NAME', QUEUE_NAME)

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
LOGGING_LEVEL = os.environ.get('SYSTEM_LOGGING_LEVEL', 'INFO').upper()

if LOGGING_LEVEL == "DEBUG":
    LOGGING = LOG_CONSOLE_DEBUG
elif LOGGING_LEVEL == "WARNING":
    LOGGING = LOG_CONSOLE_WARNING
elif LOGGING_LEVEL == "ERROR":
    LOGGING = LOG_CONSOLE_ERROR
elif LOGGING_LEVEL == "CRITICAL":
    LOGGING = LOG_CONSOLE_CRITICAL
else:
    LOGGING = LOG_CONSOLE_INFO #default

# Base URL of vault or DCOS secrets store, or None to disable secrets
SECRETS_URL = os.environ.get('SECRETS_URL', None)
# Public token if DCOS secrets store, or privileged token for vault
SECRETS_TOKEN = os.environ.get('SECRETS_TOKEN', None)
# DCOS service account name, or None if not DCOS secrets store
DCOS_SERVICE_ACCOUNT = os.environ.get('DCOS_SERVICE_ACCOUNT', None)
# Flag for raising SSL warnings associated with secrets transactions.
SECRETS_SSL_WARNINGS = os.environ.get('SECRETS_SSL_WARNINGS', 'true').lower() not in ('no', 'false', 'f', '0')
