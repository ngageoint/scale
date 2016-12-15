"""Defines the application configuration for the recipe application"""
from __future__ import unicode_literals

from django.apps import AppConfig


class RecipeConfig(AppConfig):
    """Configuration for the recipe app
    """
    name = 'recipe'
    label = 'recipe'
    verbose_name = 'Recipe'
