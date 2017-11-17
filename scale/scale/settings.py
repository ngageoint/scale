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

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Project version
VERSION = scale.__version__
DOCKER_VERSION = scale.__docker_version__

# Mesos connection information. Default for -m
# This can be something like "127.0.0.1:5050"
# or a zookeeper url like 'zk://host1:port1,host2:port2,.../path`
MESOS_MASTER = None

# Zookeeper URL for scheduler leader election. If this is None, only a single scheduler is used.
SCHEDULER_ZK = None

# The full name for the Scale Docker image (without version tag)
SCALE_DOCKER_IMAGE = 'geoint/scale'

# The location of the config file containing Docker credentials
# The URI value should point to an externally hosted location such as a webserver or hosted S3 bucket. The value will be an http URL such as 'http://static.mysite.com/foo/.dockercfg'
CONFIG_URI = None

# Directory for rotating metrics storage
METRICS_DIR = None

# URL for logstash, or None to disable logstash
LOGGING_ADDRESS = None
LOGGING_HEALTH_ADDRESS = None

# Base URL of elasticsearch nodes
ELASTICSEARCH_URLS = None
# Placeholder for Elasticsearch object. Needed for unit tests.
ELASTICSEARCH = None

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

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
INSECURE_DEFAULT_KEY = 'this-key-is-insecure-and-should-never-be-used-in-production'

SECRET_KEY = INSECURE_DEFAULT_KEY

# Security settings for production
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
# If both are set to values other than None, scheduler will attempt to make remote debugger connection on launch
DEBUG_HOST = None
DEBUG_PORT = 1337

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
    # Scale apps
    'batch',
    'cli',
    'diagnostic',
    'error',
    'ingest',
    'job',
    'mesos_api',
    'messaging',
    'metrics',
    'node',
    'port',
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
            ],
        },
    },
]

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.DjangoFilterBackend',
    ),
    'DEFAULT_PAGINATION_CLASS': 'util.rest.DefaultPagination',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework.renderers.AdminRenderer',
    ),
    'ALLOWED_VERSIONS': ('v4', 'v5', 'v6'),
    'DEFAULT_VERSION': 'v5',
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
}

ROOT_URLCONF = 'scale.urls'

WSGI_APPLICATION = 'scale.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = 'static/'

# Additional locations of static files

STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
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
    'file-debug': {
        'level': 'DEBUG',
        'class': 'logging.handlers.TimedRotatingFileHandler',
        'formatter': 'standard',
        'filename': os.path.join(LOG_DIR, '%s_debug.log' % LOG_NAME),
        'when': 'midnight'
    },
    'file-info': {
        'level': 'INFO',
        'class': 'logging.handlers.TimedRotatingFileHandler',
        'formatter': 'standard',
        'filename': os.path.join(LOG_DIR, '%s_info.log' % LOG_NAME),
        'when': 'midnight'
    },
    'file-error': {
        'level': 'ERROR',
        'class': 'logging.handlers.TimedRotatingFileHandler',
        'formatter': 'standard',
        'filename': os.path.join(LOG_DIR, '%s_errors.log' % LOG_NAME),
        'when': 'midnight'
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
LOG_CONSOLE_FILE_DEBUG = {
    'version': 1,
    'formatters': LOG_FORMATTERS,
    'filters': LOG_FILTERS,
    'handlers': LOG_HANDLERS,
    'loggers': {
        '': {
            'handlers': ['console', 'console-stderr', 'file-debug', 'file-info', 'file-error'],
            'level': 'DEBUG',
        },
    },
}
LOG_CONSOLE_FILE_INFO = {
    'version': 1,
    'formatters': LOG_FORMATTERS,
    'filters': LOG_FILTERS,
    'handlers': LOG_HANDLERS,
    'loggers': {
        '': {
            'handlers': ['console', 'console-stderr', 'file-info', 'file-error'],
            'level': 'INFO',
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
