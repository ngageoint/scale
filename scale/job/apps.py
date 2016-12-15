"""Defines the application configuration for the job application"""
from django.apps import AppConfig


class JobConfig(AppConfig):
    """Configuration for the job app
    """
    name = u'job'
    label = u'job'
    verbose_name = u'Job'
