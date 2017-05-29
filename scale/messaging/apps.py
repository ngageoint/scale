"""Defines the application configuration for the scale messaging application"""
from __future__ import unicode_literals
from django.apps import AppConfig


class MessagingConfig(AppConfig):
    """Configuration for the metrics app"""
    name = 'messaging'
    label = 'messaging'
    verbose_name = 'Message passing'

    def ready(self):
        """Registers the messaging factory methods."""
        # import storage.brokers.factory as factory
        #


        # from storage.brokers.host_broker import HostBroker
        # from storage.brokers.nfs_broker import NfsBroker
        # from storage.brokers.s3_broker import S3Broker
        #
        # # Register broker types
        # factory.add_broker_type(HostBroker)
        # factory.add_broker_type(NfsBroker)
        # factory.add_broker_type(S3Broker)
        #
        # # Register storage errors
        # from error.exceptions import register_error
        # from storage.exceptions import DeletedFile, MissingFile
        #
        # register_error(DeletedFile(''))
        # register_error(MissingFile(''))
        pass
