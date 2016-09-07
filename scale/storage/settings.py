"""Defines all the custom settings used by this application."""

from django.conf import settings

# S3 file storage options
S3_STORAGE_CLASS = getattr(settings, 'S3_STORAGE_CLASS', 'STANDARD')  # (STANDARD, REDUCED_REDUNDANCY)
S3_SERVER_SIDE_ENCRYPTION = getattr(settings, 'S3_SERVER_SIDE_ENCRYPTION', None)  # (None, AES256)

# Defined to allow local mock S3 service
S3_ADDRESSING_STYLE = getattr(settings, 'S3_ADDRESSING_STYLE', 'auto')

# Max number of retries for recoverable download errors
S3_RETRY_COUNT = getattr(settings, 'S3_RETRY_COUNT', 3)

# The delay between retry attempts
S3_RETRY_DELAY = getattr(settings, 'S3_RETRY_DELAY', 60)  # 1 minute
