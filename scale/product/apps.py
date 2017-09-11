"""Defines the application configuration for the product application"""
from __future__ import unicode_literals

from django.apps import AppConfig


class ProductConfig(AppConfig):
    """Configuration for the product application"""
    name = 'product'
    label = 'product'
    verbose_name = 'Product'

    def ready(self):
        """Registers the product implementations with other applications."""

        from job.configuration.data.data_file import DATA_FILE_STORE
        from product.configuration.product_data_file import ProductDataFileStore

        # Register product files for the data file store
        DATA_FILE_STORE['DATA_FILE_STORE'] = ProductDataFileStore()
