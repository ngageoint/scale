from __future__ import unicode_literals

import django
from django.core.management import call_command
from django.test import TestCase
# from rest_framework import status
# from mock import patch


from messaging.backends.amqp import AMQPMessagingBackend
from messaging.backends.factory import add_message_backend

class TestScaleIfCommand(TestCase):
    fixtures = ['diagnostic_job_types.json', 'diagnostic_recipe_types.json']

    def setUp(self):
        django.setup()

        add_message_backend(AMQPMessagingBackend)

    def test_handle(self):
        call_command('scale_if')