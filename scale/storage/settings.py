"""Defines all the custom settings used by this application."""

import os

from django.conf import settings

_aws_access_key_id = os.environ['AWS_ACCESS_KEY_ID'] if 'AWS_ACCESS_KEY_ID' in os.environ else None
S3_ACCESS_KEY_ID_DEFAULT = getattr(settings, 'S3_ACCESS_KEY_ID_DEFAULT', _aws_access_key_id)
_aws_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY'] if 'AWS_SECRET_ACCESS_KEY' in os.environ else None
S3_SECRET_ACCESS_KEY_DEFAULT = getattr(settings, 'S3_SECRET_ACCESS_KEY_DEFAULT', _aws_secret_access_key)

# S3 file storage options
S3_STORAGE_CLASS = getattr(settings, 'S3_STORAGE_CLASS', 'STANDARD')
S3_ENCRYPTED = getattr(settings, 'S3_ENCRYPTED', False)

# Defined to allow local mock S3 service
S3_CALLING_FORMAT = getattr(settings, 'S3_CALLING_FORMAT', None)
S3_SECURE = getattr(settings, 'S3_SECURE', True)
S3_HOST = getattr(settings, 'S3_HOST', None)
S3_PORT = getattr(settings, 'S3_PORT', None)

# Max number of retries for recoverable download errors
S3_RETRY_COUNT = getattr(settings, 'S3_RETRY_COUNT', 3)

# The delay between retry attempts
S3_RETRY_DELAY = getattr(settings, 'S3_RETRY_DELAY', 60)  # 1 minute
