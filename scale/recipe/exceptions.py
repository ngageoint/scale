"""Defines exceptions that can occur when interacting with recipes and recipe types"""


class CreateRecipeError(Exception):
    """Exception indicating that a recipe cannot be created"""
    pass


class ReprocessError(Exception):
    """Exception indicating that a reprocessing request cannot be completed"""
    pass


class SupersedeError(Exception):
    """Exception indicating that a recipe cannot be superseded"""
    pass
