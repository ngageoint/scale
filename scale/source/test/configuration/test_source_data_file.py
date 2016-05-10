from __future__ import unicode_literals

import datetime

import django
from django.utils.timezone import now
from django.test import TestCase
from mock import call, patch

from source.configuration.source_data_file import SourceDataFileParseSaver
from source.models import SourceFile
from storage.models import Workspace
from util.parse import parse_datetime


class TestSourceDataFileParseSaverSaveParseResults(TestCase):

    def setUp(self):
        django.setup()

        self.workspace = Workspace.objects.create(name='Test workspace')
        self.file_name_1 = 'my_file.txt'
        self.media_type_1 = 'text/plain'
        self.source_file_1 = SourceFile.objects.create(file_name=self.file_name_1, media_type=self.media_type_1, file_size=10,
                                                       data_type='Dummy', file_path='the_path', workspace=self.workspace)
        self.file_name_2 = 'my_file.json'
        self.media_type_2 = 'application/json'
        self.source_file_2 = SourceFile.objects.create(file_name=self.file_name_2, media_type=self.media_type_2, file_size=10,
                                                       data_type='Dummy', file_path='the_path', workspace=self.workspace)

        self.extra_source_file_id = 99999

    @patch('source.configuration.source_data_file.SourceFile.objects.save_parse_results')
    def test_successful(self, mock_save):
        """Tests calling SourceDataFileParseSaver.save_parse_results() successfully"""

        geo_json = {'type': 'Feature'}
        started = now()
        ended = started + datetime.timedelta(days=1)
        # quick hack to give these a valid timezone. Easier than creating a TZ object since we don't really care about the time for this test.
        started = parse_datetime(started.isoformat() + "Z")
        ended = parse_datetime(ended.isoformat() + "Z")

        file_ids = [self.source_file_1.id, self.source_file_2.id, self.extra_source_file_id]
        parse_results = {self.file_name_1: (geo_json, started, None, [], None),
                         self.file_name_2: (None, None, ended, [], None),
                         'FILE_WITH_NO_SOURCE_FILE_MODEL': (None, None, None, None, None)}
        
        SourceDataFileParseSaver().save_parse_results(parse_results, file_ids)
        
        calls = [call(self.source_file_1.id, geo_json, started, None, [], None),
                 call(self.source_file_2.id, None, None, ended, [], None)]
        
        self.assertEqual(mock_save.call_count, 2)
        mock_save.assert_has_calls(calls, any_order=True)
