#@PydevCodeAnalysisIgnore
import django
import json
import sys

from django.test.testcases import TransactionTestCase
from mock import patch, Mock, MagicMock
from unittest.case import skipIf

from mesos_api.api import SlaveInfo
from node.models import Node

if not sys.platform.startswith("win"):
    import scheduler

@skipIf(sys.platform.startswith("win"), u'The scheduler uses the mesos native api.'
        '  Our development environment does not have this available on windows')
class TestScheduler(TransactionTestCase):
    '''An integration test of the queue depth view'''

    def setUp(self):
        django.setup()

        #mock out threading.start

    @patch('scheduler.scale_scheduler.initialize_system')
    @patch('scheduler.scale_scheduler.threading.Thread.start')
    def _get_mocked_scheduler_driver_master(self, _m1, _m2):
        '''gets a registered scheduler with some stuff mocked out for testing'''
        return self._get_registered_scheduler_driver_master()

    def _get_registered_scheduler_driver_master(self):
        driver = Mock()
        framework_id = Mock()
        framework_id.value = 'framework_id'
        master_info = Mock()
        master_info.hostname = 'localhost'
        master_info.port = 1234

        my_scheduler = scheduler.scale_scheduler.ScaleScheduler(None)
        my_scheduler.registered(driver,framework_id,master_info)
        return my_scheduler, driver, master_info

    @patch('scheduler.scale_scheduler.initialize_system')
    @patch('scheduler.scale_scheduler.threading.Thread.start')
    def testRegistration(self, mock_thread_start, mock_initializer):
        my_scheduler, driver, master_info = self._get_registered_scheduler_driver_master()
        self.assertTrue(mock_initializer.called,'initializer should be called on registration')
        self.assertEqual(mock_thread_start.call_count, 3,
                        'reconciliation and job kill threads should be started (2 != %d)' % mock_thread_start.call_count)

    @patch('scheduler.scale_scheduler.ScaleScheduler._reconcile_running_jobs')
    def test_reregistration_triggers_reconciliation(self, mock_reconcile_running_jobs):
        my_scheduler, driver, master_info = self._get_mocked_scheduler_driver_master()
        reconcile_calls_before = mock_reconcile_running_jobs.call_count
        my_scheduler.reregistered(driver,master_info)
        reconcile_calls_after = mock_reconcile_running_jobs.call_count
        self.assertEqual(reconcile_calls_after - reconcile_calls_before, 1,
                         're-registering the scheduler should trigger a call to reconcile running jobs')

    '''TODO: add more tests, perhaps these:    
    def test_resource_offers_updates_nodes(self):
        pass

    def test_resource_offers_schedules_next_job(self):
        pass

    def test_resource_offers_gets_next_task(self):
        pass

    def test_status_update_reconcile(self):
        pass

    def test_status_update_running(self):
        pass

    def test_status_update_finished(self):
        pass

    def test_status_update_lost(self):
        pass

    def test_framework_message_no_node(self):
        pass

    def test_slave_lost_removes_running_jobs(self):
        pass
    '''

