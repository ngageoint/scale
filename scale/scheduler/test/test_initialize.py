from __future__ import unicode_literals

import django

from django.test.testcases import TransactionTestCase
from mock import patch

from job.models import Job, JobType
from scheduler.initialize import initialize_system
from messaging.backends.amqp import AMQPMessagingBackend
from messaging.backends.factory import add_message_backend


class TestInitializeSystem(TransactionTestCase):

    fixtures = ['basic_system_job_types.json']

    def setUp(self):
        django.setup()

        add_message_backend(AMQPMessagingBackend)

    @patch('scheduler.initialize.CommandMessageManager')
    def test_create_clock_job(self, mock_msg_mgr):
        """Tests creating the Scale clock job"""

        clock_job_type = JobType.objects.get_clock_job_type()
        count = Job.objects.filter(job_type_id=clock_job_type.id).count()
        self.assertEqual(count, 0)

        initialize_system()
        count = Job.objects.filter(job_type_id=clock_job_type.id).count()
        self.assertEqual(count, 1)

        # Make sure it only creates one job
        initialize_system()
        count = Job.objects.filter(job_type_id=clock_job_type.id).count()
        self.assertEqual(count, 1)
