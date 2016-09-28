"""Defines the application configuration for the batch application"""
from __future__ import unicode_literals

from django.apps import AppConfig


class BatchConfig(AppConfig):
    """Configuration for the batch app"""
    name = 'batch'
    label = 'batch'
    verbose_name = 'Batch'
