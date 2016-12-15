"""Defines the application configuration for the recipe application"""
from django.apps import AppConfig


class RecipeConfig(AppConfig):
    """Configuration for the recipe app
    """
    name = u'recipe'
    label = u'recipe'
    verbose_name = u'Recipe'
