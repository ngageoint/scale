from __future__ import unicode_literals

import django
from django.test import TestCase

from util.host import host_address_from_mesos_url


class TestUrlExtraction(TestCase):
    def setUp(self):
        django.setup()

    def test_http_url(self):
        result = host_address_from_mesos_url('http://leader.mesos:80/mesos')
        self.assertEquals(result.protocol, 'http')
        self.assertEquals(result.hostname, 'leader.mesos')
        self.assertEquals(result.port, 80)

    def test_https_url(self):
        result = host_address_from_mesos_url('https://leader.mesos:5050/mesos')
        self.assertEquals(result.protocol, 'https')
        self.assertEquals(result.hostname, 'leader.mesos')
        self.assertEquals(result.port, 5050)

    def test_http_no_port(self):
        result = host_address_from_mesos_url('http://leader.mesos/mesos')
        self.assertEquals(result.protocol, 'http')
        self.assertEquals(result.hostname, 'leader.mesos')
        self.assertEquals(result.port, 80)

    def test_https_no_port(self):
        result = host_address_from_mesos_url('https://leader.mesos/mesos')
        self.assertEquals(result.protocol, 'https')
        self.assertEquals(result.hostname, 'leader.mesos')
        self.assertEquals(result.port, 443)
