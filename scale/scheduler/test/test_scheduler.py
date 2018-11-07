from __future__ import absolute_import
from __future__ import unicode_literals

import django

from django.test.testcases import TransactionTestCase
from mock import patch, Mock

from messaging.backends.amqp import AMQPMessagingBackend
from messaging.backends.factory import add_message_backend

from scheduler.scale_scheduler import ScaleScheduler


class TestScheduler(TransactionTestCase):
    """Tests core functionality of the scheduler."""

    def setUp(self):
        django.setup()

        add_message_backend(AMQPMessagingBackend)

        # mock out threading.start

    @patch('scheduler.scale_scheduler.initialize_system')
    @patch('scheduler.scale_scheduler.threading.Thread.start')
    def _get_mocked_scheduler_driver_master(self, _m1, _m2):
        """gets a registered scheduler with some stuff mocked out for testing"""
        return self._get_registered_scheduler_driver_master()

    def _get_registered_scheduler_driver_master(self):
        driver = Mock()
        driver.framework_id.value = 'framework_id'
        driver.mesos_url = 'http://localhost'

        my_scheduler = ScaleScheduler()
        my_scheduler.initialize()
        my_scheduler.subscribed(driver)
        return my_scheduler, driver

    @patch('scheduler.scale_scheduler.initialize_system')
    @patch('scheduler.scale_scheduler.threading.Thread.start')
    def testRegistration(self, mock_thread_start, mock_initializer):
        my_scheduler, driver  = self._get_registered_scheduler_driver_master()
        self.assertTrue(mock_initializer.called, 'initializer should be called on registration')
        self.assertEqual(
            mock_thread_start.call_count, 7,
            '7 threads should be started (7 != %d)' % mock_thread_start.call_count
        )

    @patch('scheduler.scale_scheduler.ScaleScheduler._reconcile_running_jobs')
    def test_reregistration_triggers_reconciliation(self, mock_reconcile_running_jobs):
        my_scheduler, driver = self._get_mocked_scheduler_driver_master()
        reconcile_calls_before = mock_reconcile_running_jobs.call_count
        my_scheduler.subscribed(driver)
        reconcile_calls_after = mock_reconcile_running_jobs.call_count
        self.assertEqual(reconcile_calls_after - reconcile_calls_before, 1,
                         're-registering the scheduler should trigger a call to reconcile running jobs')
