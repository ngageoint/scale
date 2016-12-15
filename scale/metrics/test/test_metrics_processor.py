from __future__ import unicode_literals

import django
from django.conf import settings
from django.test import TestCase
from mock import patch
from unittest.case import skipIf
import shutil
import sys
import tempfile

from metrics.metrics_processor import MetricsProcessor
from node.models import Node

from StringIO import StringIO

@skipIf(sys.platform.startswith("win"), 'rrdtool is not available on windows.')
class TestMetricsProcessor(TestCase):

    def setUp(self):
        """Setup test harness"""
        django.setup()
        settings.METRICS_DIR = tempfile.mkdtemp()

        Node.objects.register_node('test_host1', 5051, 'test_host1_id')

    def tearDown(self):
        """Tear down the test harness"""
        shutil.rmtree(settings.METRICS_DIR)

    @patch('urllib2.urlopen')
    def test_metrics_processor(self, urlopen):
        """This method tests the Metrics Processor"""

        urlopen.return_value = StringIO("""{"slave\/mem_used":31360,"system\/mem_free_bytes":6298882048}""")
        metrics_process = MetricsProcessor()
        
        metrics_process.query_metrics()
