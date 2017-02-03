"""The scale error application"""
from __future__ import unicode_literals

from django.apps import AppConfig


class ErrorConfig(AppConfig):
    """Configuration for the error app
    """
    name = 'error'
    label = 'error'
    verbose_name = 'Error'

    def ready(self):
        """Registers basic errors"""
        from error.exceptions import ScaleDatabaseError, ScaleIOError, ScaleOperationalError, register_error

        register_error(ScaleDatabaseError())
        register_error(ScaleIOError())
        register_error(ScaleOperationalError())
