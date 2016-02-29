"""
Django settings for scale_test project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# These are used to build the commands executed by mesos for pre/post tasks, etc.
# They should be automatically set to the executable and manage.py used to
# start the mesos scheduler. If you need to use different settings, override
# in the local settings.
import sys
PYTHON_EXECUTABLE = sys.executable
MANAGE_FILE = os.path.join(BASE_DIR, 'manage.py')

# Mesos connection information. Default for -m
# This can be something like "127.0.0.1:5050"
# or a zookeeper url like 'zk://host1:port1,host2:port2,.../path`
MESOS_MASTER = None

# Zookeeper URL for scheduler leader election. If this is None, only a single not is used and election isn't performed.
SCHEDULER_ZK = None

# Directory for rotating metrics storage
METRICS_DIR = None

# Base URL for influxdb access in the form http://<machine>:8086/db/<cadvisor_db_name>/series?u=<username>&p=<password>&
# An invalid or None entry will disable gathering of these statistics
INFLUXDB_BASE_URL = None

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# If this is true, we don't delete the job_dir after it is finished.
# This might fill up the disk but can be useful for debugging.
SKIP_CLEANUP_JOB_DIR = False

TEMPLATE_DEBUG = False

ALLOWED_HOSTS = []

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
    'util',
    'mesos_api',
    'error',
    'trigger',
    'node',
    'storage',
    'job',
    'source',
    'product',
    'shared_resource',
    'recipe',
    'queue',
    'ingest',
    'scheduler',
    'metrics',
    'port',
)

MIDDLEWARE_CLASSES = (
    'util.middleware.MultipleProxyMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

REST_FRAMEWORK = {
    'PAGINATE_BY': 100,
    'PAGINATE_BY_PARAM': 'page_size',
    'MAX_PAGINATE_BY': 1000,
    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',)
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
LOG_NAME = 'scale'  # This environment var can be set
if 'LOG_NAME' in os.environ:
    LOG_NAME = os.environ['LOG_NAME']
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
    }
}
LOG_HANDLERS = {
    'null': {
        'level': 'DEBUG',
        'class': 'django.utils.log.NullHandler',
    },
    'console': {
        'level': 'DEBUG',
        'class': 'logging.StreamHandler',
        'formatter': 'standard',
        'stream': sys.stdout
    },
    'console-err': {
        'level': 'WARNING',
        'class': 'logging.StreamHandler',
        'formatter': 'standard',
        'stream': sys.stderr
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
LOG_CONSOLE_FILE_DEBUG = {
    'version': 1,
    'formatters': LOG_FORMATTERS,
    'filters': LOG_FILTERS,
    'handlers': LOG_HANDLERS,
    'loggers': {
        '': {
            'handlers': ['console', 'console-err', 'file-debug', 'file-info', 'file-error'],
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
            'handlers': ['console', 'console-err', 'file-info', 'file-error'],
            'level': 'INFO',
        },
    },
}
LOGGING = LOG_CONSOLE_FILE_INFO


# Hack to fix ISO8601 for datetime filters.
# This should be taken care of by a future django fix.  And might even be handled
# by a newer version of django-rest-framework.  Unfortunately, both of these solutions
# will accept datetimes without timezone information which we do not want to allow
# see https://code.djangoproject.com/tickets/23448
# Solution modified from http://akinfold.blogspot.com/2012/12/datetimefield-doesnt-accept-iso-8601.html
from django.forms import fields
from util.parse import parse_datetime
fields.DateTimeField.strptime = lambda _self, datetime_string, _format: parse_datetime(datetime_string)
