"""Defines the application configuration for the batch application"""
from __future__ import unicode_literals

from django.apps import AppConfig


class BatchConfig(AppConfig):
    """Configuration for the batch app"""
    name = 'batch'
    label = 'batch'
    verbose_name = 'Batch'

    def ready(self):
        """Registers components related to batches"""

        # Register batch message types
        from batch.messages.create_batch_recipes import CreateBatchRecipes
        from batch.messages.update_batch_metrics import UpdateBatchMetrics
        from messaging.messages.factory import add_message_type

        add_message_type(CreateBatchRecipes)
        add_message_type(UpdateBatchMetrics)
