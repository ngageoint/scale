"""Defines the classes for handling recipe type logic"""
from __future__ import unicode_literals


class RecipeTypeHandler(object):
    """Handles the logic for a recipe type, such as operations on the recipe graph defined by the recipe type definition
    """

    def __init__(self, definition):
        """Creates a recipe definition object from the given dictionary. The general format is checked for correctness,
        but the actual job details are not checked for correctness.

        :param definition: The recipe definition
        :type definition: dict

        :raises InvalidDefinition: If the given definition is invalid
        """

        self._definition = definition
