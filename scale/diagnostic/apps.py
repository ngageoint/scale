"""Defines the application configuration for the diagnostic application"""
from __future__ import unicode_literals

from django.apps import AppConfig


class DiagnosticConfig(AppConfig):
    """Configuration for the diagnostic app
    """

    name = 'diagnostic'
    label = 'diagnostic'
    verbose_name = 'Diagnostic'
