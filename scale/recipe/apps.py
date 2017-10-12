"""Defines the application configuration for the recipe application"""
from __future__ import unicode_literals

from django.apps import AppConfig


class RecipeConfig(AppConfig):
    """Configuration for the recipe app
    """
    name = 'recipe'
    label = 'recipe'
    verbose_name = 'Recipe'

    def ready(self):
        """Registers components related to recipes"""

        # Register recipe message types
        from messaging.messages.factory import add_message_type
        from recipe.messages.update_recipes import UpdateRecipes

        add_message_type(UpdateRecipes)
