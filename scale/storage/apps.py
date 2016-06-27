"""Defines the configuration for the storage application"""
from __future__ import unicode_literals
from django.apps import AppConfig


class StorageConfig(AppConfig):
    """Configuration for the storage app"""
    name = 'storage'
    label = 'storage'
    verbose_name = 'Storage'

    def ready(self):
        """Registers the storage brokers with the broker system."""
        import storage.brokers.factory as factory

        from storage.brokers.host_broker import HostBroker
        from storage.brokers.nfs_broker import NfsBroker
        from storage.brokers.s3_broker import S3Broker

        # Register broker types
        factory.add_broker_type(HostBroker)
        factory.add_broker_type(NfsBroker)
        factory.add_broker_type(S3Broker)
