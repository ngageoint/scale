'''Defines the application configuration for the product application'''
from django.apps import AppConfig


class ProductConfig(AppConfig):
    '''Configuration for the product application'''
    name = u'product'
    label = u'product'
    verbose_name = u'Product'

    def ready(self):
        '''Registers the product implementations with other applications.'''

        from job.configuration.data.data_file import DATA_FILE_STORE
        from product.configuration.product_data_file import ProductDataFileStore
        from product.queue_processor import ProductProcessor
        from queue.models import Queue

        # Register product files for the data file store
        DATA_FILE_STORE[u'DATA_FILE_STORE'] = ProductDataFileStore()

        # Register the queue processor for publishing products
        Queue.objects.register_processor(ProductProcessor)
