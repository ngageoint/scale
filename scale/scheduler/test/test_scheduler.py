from __future__ import absolute_import
from __future__ import unicode_literals

import django

from django.conf import settings
from django.test.testcases import TransactionTestCase
from mesoshttp.offers import Offer
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

    @patch('scheduler.manager.SchedulerManager.add_new_offer_count')
    @patch('scheduler.resources.manager.ResourceManager.add_new_offers')
    @patch('scheduler.node.manager.NodeManager.register_agents')
    def test_offer_match_against_matched_and_unmatched(self, register_agents, add_new_offers, add_new_offer_count):
        """Validate resource reservations that don't match with ACCEPTED_RESOURCE_ROLE are ignored"""

        settings.ACCEPTED_RESOURCE_ROLE = 'service-account'

        offers_json = {u'offers': {u'offers': [
            {u'domain': {u'fault_domain': {u'region': {u'name': u'us-east-2'}, u'zone': {u'name': u'us-east-2a'}}},
             u'url': {u'path': u'/slave(1)', u'scheme': u'http',
                      u'address': {u'ip': u'172.12.4.140', u'hostname': u'172.12.4.140', u'port': 5051}},
             u'hostname': u'172.12.4.140', u'framework_id': {u'value': u'6777f785-2d17-4a2c-9e06-2bf56efa3417-0003'},
             u'agent_id': {u'value': u'6777f785-2d17-4a2c-9e06-2bf56efa3417-S3'},
             u'id': {u'value': u'6777f785-2d17-4a2c-9e06-2bf56efa3417-O1693'}, u'resources': [
                {u'role': u'service-account', u'scalar': {u'value': 4.0}, u'type': u'SCALAR', u'name': u'cpus',
                 u'reservation': {u'principal': u'service-account'}}, {u'ranges': {
                    u'range': [{u'begin': 1025, u'end': 2180}, {u'begin': 2182, u'end': 3887},
                               {u'begin': 3889, u'end': 5049}, {u'begin': 5052, u'end': 8079},
                               {u'begin': 8082, u'end': 8180}, {u'begin': 8182, u'end': 32000}]},
                    u'role': u'service-account', u'type': u'RANGES',
                    u'name': u'ports', u'reservation': {
                        u'principal': u'service-account'}},
                {u'role': u'service-account', u'scalar': {u'value': 119396.0}, u'type': u'SCALAR', u'name': u'disk',
                 u'reservation': {u'principal': u'service-account'}},
                {u'role': u'service-account', u'scalar': {u'value': 14861.0}, u'type': u'SCALAR', u'name': u'mem',
                 u'reservation': {u'principal': u'service-account'}}]},
            {u'domain': {u'fault_domain': {u'region': {u'name': u'us-east-2'}, u'zone': {u'name': u'us-east-2a'}}},
             u'url': {u'path': u'/slave(1)', u'scheme': u'http',
                      u'address': {u'ip': u'172.12.4.140', u'hostname': u'172.12.4.140', u'port': 5051}},
             u'hostname': u'172.12.4.140', u'framework_id': {u'value': u'6777f785-2d17-4a2c-9e06-2bf56efa3417-0003'},
             u'agent_id': {u'value': u'6777f785-2d17-4a2c-9e06-2bf56efa3417-S3'},
             u'id': {u'value': u'6777f785-2d17-4a2c-9e06-2bf56efa3417-O1693'}, u'resources': [
                {u'role': u'*', u'scalar': {u'value': 4.0}, u'type': u'SCALAR', u'name': u'cpus'}, {u'ranges': {
                    u'range': [{u'begin': 1025, u'end': 2180}, {u'begin': 2182, u'end': 3887},
                               {u'begin': 3889, u'end': 5049}, {u'begin': 5052, u'end': 8079},
                               {u'begin': 8082, u'end': 8180}, {u'begin': 8182, u'end': 32000}]},
                    u'role': u'*', u'type': u'RANGES',
                    u'name': u'ports'},
                {u'role': u'*', u'scalar': {u'value': 119396.0}, u'type': u'SCALAR', u'name': u'disk'},
                {u'role': u'*', u'scalar': {u'value': 14861.0}, u'type': u'SCALAR', u'name': u'mem'}]}
        ]}, u'type': u'OFFERS'}

        offers = [Offer('', '', '', x) for x in offers_json['offers']['offers']]

        ScaleScheduler().offers(offers)

        register_agents.called_with(['6777f785-2d17-4a2c-9e06-2bf56efa3417-S3'])
        add_new_offer_count.called_with(1)
        self.assertEquals(add_new_offers.call_count, 1)