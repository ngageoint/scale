"""
Django settings for scale_test project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

import os
import scale
import sys

import dj_database_url


def get_env_boolean(variable_name, default=False):
    return os.getenv(variable_name,  str(default)).lower() in ('yes', 'true', 't', '1')


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Project version
VERSION = scale.__version__
DOCKER_VERSION = scale.__docker_version__

# Mesos connection information. Default for -m
# This can be something like "127.0.0.1:5050"
# or a zookeeper url like 'zk://host1:port1,host2:port2,.../path`
MESOS_MASTER = os.getenv('MESOS_MASTER', 'zk://leader.mesos:2181/mesos')

# We by default, use the '*' role, meaning all resources are unreserved offers are received
# By default, use the '*' role, meaning all resources are unreserved offers are received
MESOS_ROLE = os.getenv('MESOS_ROLE', '*')

# Used to set the user that Mesos tasks are launched by Docker. This should NEVER be set to root
# and must be a user name NOT a Linux UID. Mesos chokes on UIDs.
CONTAINER_PROCESS_OWNER = os.getenv('CONTAINER_PROCESS_OWNER', 'nobody')

# By default, the accepted resources match reservations to the MESOS_ROLE
ACCEPTED_RESOURCE_ROLE = os.getenv('ACCEPTED_RESOURCE_ROLE', MESOS_ROLE)

# By default, all API calls require authentication.
PUBLIC_READ_API = get_env_boolean('PUBLIC_READ_API')

# Placeholder for service secret that will be overridden in local_settings_docker
SERVICE_SECRET = None

# Zookeeper URL for scheduler leader election. If this is None, only a single scheduler is used.
SCHEDULER_ZK = None

# The full name for the Scale Docker image (without version tag)
SCALE_DOCKER_IMAGE = 'geoint/scale'

# The location of the config file containing Docker credentials
# The URI value should point to an externally hosted location such as a webserver or hosted S3 bucket.
# The value will be an http URL such as 'http://static.mysite.com/foo/.dockercfg'
CONFIG_URI = None

# Directory for rotating metrics storage
METRICS_DIR = None

# URL for fluentd, or None to disable fluentd
LOGGING_ADDRESS = None
LOGGING_HEALTH_ADDRESS = None

# Base URL of elasticsearch nodes
ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
# Placeholder for elasticsearch version. Supplied in production by local_settings_docker.py
ELASTICSEARCH_VERSION = None
# Placeholder for Elasticsearch object. Needed for unit tests.
ELASTICSEARCH = None

DATABASE_URL = os.getenv('DATABASE_URL')

# Broker URL for connection to messaging backend
BROKER_URL = 'amqp://guest:guest@localhost:5672//'
QUEUE_NAME = 'scale-command-messages'

# Base URL of vault or DCOS secrets store, or None to disable secrets
SECRETS_URL = None
# Public token if DCOS secrets store, or privleged token for vault
SECRETS_TOKEN = None
# DCOS service account name, or None if not DCOS secrets store
DCOS_SERVICE_ACCOUNT = None
# Flag for raising SSL warnings associated with secrets transactions.
SECRETS_SSL_WARNINGS = True

# SECURITY WARNING: keep the secret key used in production secret!
INSECURE_DEFAULT_KEY = 'this-key-is-insecure-and-should-never-be-used-in-production'

SECRET_KEY = INSECURE_DEFAULT_KEY

# Used to write the superuser password
MESOS_SANDBOX = os.getenv('MESOS_SANDBOX')

# Security settings for production
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = get_env_boolean('SESSION_COOKIE_SECURE', True)
X_FRAME_OPTIONS = 'DENY'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# authentication toggle, to be used for testing
AUTHENTICATION_ENABLED = get_env_boolean('AUTHENTICATION_ENABLED', True)

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'rest_framework',
    'rest_framework.authtoken',

    ###############
    # Social Auth #
    ###############
    'oauth2_provider',
    'social_django',
    'rest_framework_social_oauth2',

    # Scale apps
    'accounts',
    'batch',
    'cli',
    'data',
    'dataset',
    'diagnostic',
    'error',
    'ingest',
    'job',
    'mesos_api',
    'messaging',
    'metrics',
    'node',
    'product',
    'queue',
    'recipe',
    'scheduler',
    'shared_resource',
    'source',
    'storage',
    'trigger',
    'util',
    'vault'
)

MIDDLEWARE = [
    'util.middleware.MultipleProxyMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'util.middleware.ExceptionLoggingMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': False,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                ###############
                # Social Auth #
                ###############
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_PAGINATION_CLASS': 'util.rest.DefaultPagination',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework.renderers.AdminRenderer',
    ),
    'ALLOWED_VERSIONS': ('v6', 'v7'),
    'DEFAULT_VERSION': 'v6',
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
}

if AUTHENTICATION_ENABLED:
    REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (        
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',

        ###############
        # Social Auth #
        ###############
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework_social_oauth2.authentication.SocialAuthentication',
    )
    
    REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = (
        'util.rest.ScaleAPIPermissions',
    )

else:
    REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = ()
    REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = ()
    REST_FRAMEWORK['UNAUTHENTICATED_USER'] = None

ROOT_URLCONF = 'scale.urls'

WSGI_APPLICATION = 'scale.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases


DATABASES = {
    'default': dj_database_url.config(default='sqlite://%s' % os.path.join(BASE_DIR, 'db.sqlite3'))
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOGIN_REDIRECT_URL = '/'

#############################
# GEOAxIS specific settings #
#############################
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/'
# Redirect after directly hitting login endpoint
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/'
DEFAULT_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.mail.mail_validation',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details'
)

SOCIAL_AUTH_GEOAXIS_KEY = os.getenv('GEOAXIS_KEY')
SOCIAL_AUTH_GEOAXIS_SECRET = os.getenv('GEOAXIS_SECRET')
SOCIAL_AUTH_GEOAXIS_HOST = os.getenv('GEOAXIS_HOST', 'geoaxis.gxaccess.com')
OAUTH_GEOAXIS_USER_FIELDS = os.getenv(
    'GEOAXIS_USER_FIELDS', 'username, email, last_name, first_name')
SOCIAL_AUTH_GEOAXIS_USER_FIELDS = map(
    str.strip, OAUTH_GEOAXIS_USER_FIELDS.split(','))
OAUTH_GEOAXIS_SCOPES = os.getenv('GEOAXIS_SCOPES', 'UserProfile.me')
SOCIAL_AUTH_GEOAXIS_SCOPE = map(str.strip, OAUTH_GEOAXIS_SCOPES.split(','))

# GeoAxisOAuth2 will cause all login attempt to fail if
# SOCIAL_AUTH_GEOAXIS_HOST is None
GEOAXIS_ENABLED = False
if SOCIAL_AUTH_GEOAXIS_KEY and len(SOCIAL_AUTH_GEOAXIS_KEY) > 0:
    GEOAXIS_ENABLED = True
    AUTHENTICATION_BACKENDS += (
        'django_geoaxis.backends.geoaxis.GeoAxisOAuth2',
    )


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = 'static/'

STATICFILES_DIRS = ()

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Logging configuration
LOG_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
LOG_NAME = 'scale'
LOG_FORMATTERS = {
    'standard': {
        'format': ('%(asctime)s %(levelname)s ' +
                   '[%(name)s(%(lineno)s)] %(message)s'),
        'datefmt': '%Y-%m-%d %H:%M:%S',
    },
    'db-standard': {
        'format': ('[%(name)s(%(lineno)s)] %(message)s'),
    }
}
LOG_FILTERS = {
    'require_debug_false': {
        '()': 'django.utils.log.RequireDebugFalse'
    },
    'debug_info_only':{
        '()':'scale.custom_logging.UserFilter',
    }
}
LOG_HANDLERS = {
    'null': {
        'level': 'DEBUG',
        'class': 'logging.NullHandler',
    },
    'mesoshttp' : {
        'level': 'DEBUG',
        'class': 'logging.StreamHandler',
        'formatter': 'standard',
        'stream': sys.stdout
    },
    'console': {
        'level': 'DEBUG',
        'class': 'logging.StreamHandler',
        'formatter': 'standard',
        'stream': sys.stdout
    },
    'console-stderr': {
        'level': 'WARNING',
        'class': 'logging.StreamHandler',
        'formatter': 'standard',
        'stream': sys.stderr
    },
    'console-stdout': {
        'level': 'DEBUG',
        'class': 'logging.StreamHandler',
        'formatter': 'standard',
        'stream': sys.stdout,
        'filters':['debug_info_only']
    },
    'log-db': {
        'level': 'WARNING',
        'class': 'error.handlers.DatabaseLogHandler',
        'formatter': 'db-standard',
        'model': 'error.models.LogEntry',
    },
}
LOG_CONSOLE_DEBUG = {
    'version': 1,
    'formatters': LOG_FORMATTERS,
    'filters': LOG_FILTERS,
    'handlers': LOG_HANDLERS,
    'loggers': {
        '': {
            'handlers': ['console-stdout','console-stderr'],
            'level': 'DEBUG',
        },
    },
}
LOG_CONSOLE_INFO = {
    'version': 1,
    'formatters': LOG_FORMATTERS,
    'filters': LOG_FILTERS,
    'handlers': LOG_HANDLERS,
    'loggers': {
        '': {
            'handlers': ['console-stdout','console-stderr'],
            'level': 'INFO',
        },
    },
}
LOG_CONSOLE_ERROR = {
    'version': 1,
    'formatters': LOG_FORMATTERS,
    'filters': LOG_FILTERS,
    'handlers': LOG_HANDLERS,
    'loggers': {
        '': {
            'handlers': ['console-stderr'],
            'level': 'ERROR',
        },
    },
}
LOG_CONSOLE_WARNING = {
    'version': 1,
    'formatters': LOG_FORMATTERS,
    'filters': LOG_FILTERS,
    'handlers': LOG_HANDLERS,
    'loggers': {
        '': {
            'handlers': ['console-stderr'],
            'level': 'WARNING',
        },
    },
}
LOG_CONSOLE_CRITICAL = {
    'version': 1,
    'formatters': LOG_FORMATTERS,
    'filters': LOG_FILTERS,
    'handlers': LOG_HANDLERS,
    'loggers': {
        '': {
            'handlers': ['console-stderr'],
            'level': 'CRITICAL',
        },
    },
}
LOGGING = LOG_CONSOLE_DEBUG

# Hack to fix ISO8601 for datetime filters.
# This should be taken care of by a future django fix.  And might even be handled
# by a newer version of django-rest-framework.  Unfortunately, both of these solutions
# will accept datetimes without timezone information which we do not want to allow
# see https://code.djangoproject.com/tickets/23448
# Solution modified from http://akinfold.blogspot.com/2012/12/datetimefield-doesnt-accept-iso-8601.html
from django.forms import fields
from util.parse import parse_datetime
fields.DateTimeField.strptime = lambda _self, datetime_string, _format: parse_datetime(datetime_string)
