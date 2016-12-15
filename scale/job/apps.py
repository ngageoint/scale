"""Defines the application configuration for the job application"""
from __future__ import unicode_literals

from django.apps import AppConfig


class JobConfig(AppConfig):
    """Configuration for the job app
    """
    name = 'job'
    label = 'job'
    verbose_name = 'Job'
