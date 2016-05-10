from __future__ import unicode_literals

import datetime
import os

import django
from django.test import TestCase
from django.utils.timezone import now
from mock import patch, MagicMock

from job.test import utils as job_utils
from source.models import SourceFile
from storage.brokers.broker import FileMove
from storage.models import Workspace
from storage.test import utils as storage_utils
from trigger.models import TriggerEvent
from trigger.test import utils as trigger_utils

FEATURE_COLLECTION_GEOJSON = {"type": "FeatureCollection", "features": [{ "type": "Feature", "properties": { "prop_a": "A", "prop_b": "B" }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 1.0, 10.5 ], [ 1.1, 21.1 ], [ 1.2, 21.2 ], [ 1.3, 21.6 ], [ 1.0, 10.5 ] ] ] } }]}
FEATURE_GEOJSON = {"type": "Feature", "properties": { "prop_a": "A", "prop_b": "B" }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 1.0, 10.5 ], [ 1.1, 21.1 ], [ 1.2, 21.2 ], [ 1.3, 21.6 ], [ 1.0, 10.5 ] ] ] } }
POLYGON_GEOJSON = {"type": "Polygon", "coordinates": [ [ [ 1.0, 10.5 ], [ 1.1, 21.1 ], [ 1.2, 21.2 ], [ 1.3, 21.6 ], [ 1.0, 10.5 ] ] ] }


class TestSourceFileManagerSaveParseResults(TestCase):

    def setUp(self):
        django.setup()

        workspace = Workspace.objects.create(name='Test Workspace', is_active=True, created=now(), last_modified=now())

        self.src_file = SourceFile.objects.create(file_name='text.txt', media_type='text/plain', file_size=10,
                                                  data_type='type', file_path='the_path', workspace=workspace)

        self.started = now()
        self.ended = self.started + datetime.timedelta(days=1)

    @patch('source.models.ScaleFile.objects.move_files')
    def test_move_source_file(self, mock_move_files):
        """Tests calling save_parse_results so that the source file is moved to a different path in the workspace"""

        new_path = os.path.join('the', 'new', 'workspace', 'path', self.src_file.file_name)

        # Call method to test
        SourceFile.objects.save_parse_results(self.src_file.id, None, None, None, [], new_path)

        # Check results
        mock_move_files.assert_called_once_with([FileMove(self.src_file, new_path)])

    @patch('source.models.ScaleFile.objects.move_files')
    def test_move_source_file_denied(self, mock_move_files):
        """Tests calling save_parse_results where the source file is not allowed to be moved within the workspace"""

        self.src_file.workspace.is_move_enabled = False
        self.src_file.workspace.save()
        new_path = os.path.join('the', 'new', 'workspace', 'path', self.src_file.file_name)

        # Call method to test
        SourceFile.objects.save_parse_results(self.src_file.id, None, None, None, [], new_path)

        # Check results
        self.assertFalse(mock_move_files.called, 'ScaleFile.objects.move_files() should not be called')

    def test_valid_feature_collection(self):
        """Tests calling save_parse_results with valid arguments"""

        # Call method to test
        SourceFile.objects.save_parse_results(self.src_file.id, FEATURE_COLLECTION_GEOJSON, self.started, self.ended,
                                              [], None)

        # Check results
        src_file = SourceFile.objects.get(pk=self.src_file.id)
        self.assertEqual(src_file.is_parsed, True)
        self.assertIsNotNone(src_file.parsed)
        self.assertEqual(src_file.data_started, self.started)
        self.assertEqual(src_file.data_ended, self.ended)
        self.assertDictEqual(src_file.meta_data, {'prop_a': 'A', 'prop_b': 'B'})
        self.assertIsNotNone(src_file.geometry)
        self.assertIsNotNone(src_file.center_point)

    def test_valid_feature(self):
        """Tests calling save_parse_results with valid arguments"""

        # Call method to test
        SourceFile.objects.save_parse_results(self.src_file.id, FEATURE_GEOJSON, self.started, self.ended, [], None)

        # Check results
        src_file = SourceFile.objects.get(pk=self.src_file.id)
        self.assertEqual(src_file.is_parsed, True)
        self.assertIsNotNone(src_file.parsed)
        self.assertEqual(src_file.data_started, self.started)
        self.assertEqual(src_file.data_ended, self.ended)
        self.assertDictEqual(src_file.meta_data, {'prop_a': 'A', 'prop_b': 'B'})
        self.assertIsNotNone(src_file.geometry)
        self.assertIsNotNone(src_file.center_point)

    def test_valid_feature_with_parse_rule(self):
        """Tests calling save_parse_results with valid arguments and parse rules in place"""

        # Setup parse rule
        workspace = storage_utils.create_workspace()
        configuration = {'version': '1.0',
                         'condition': {'media_type': 'text/plain', 'data_types': ['type']},
                         'data': {'input_data_name': 'my_input', 'workspace_name': workspace.name}}
        rule_model = trigger_utils.create_trigger_rule(trigger_type='PARSE', configuration=configuration)
        interface = {'version': '1.0', 'command': '', 'command_arguments': '', 'input_data': [{'name': 'my_input', 'type': 'file'}]}
        job_type = job_utils.create_job_type(interface=interface)
        job_type.trigger_rule = rule_model
        job_type.save()

        # Call method to test
        SourceFile.objects.save_parse_results(self.src_file.id, FEATURE_GEOJSON, self.started, self.ended, [], None)
        
        # Ensure there's an event for the parse
        evt = TriggerEvent.objects.first()
        self.assertEqual(evt.description['version'], '1.0')
        self.assertEqual(evt.description['file_name'], 'text.txt')

    def test_valid_polygon(self):
        """Tests calling save_parse_results with valid arguments"""

        # Call method to test
        SourceFile.objects.save_parse_results(self.src_file.id, POLYGON_GEOJSON, None, None, [], None)

        # Check results
        src_file = SourceFile.objects.get(pk=self.src_file.id)
        self.assertEqual(src_file.is_parsed, True)
        self.assertIsNotNone(src_file.parsed)
        self.assertIsNone(src_file.data_started)
        self.assertIsNone(src_file.data_ended)
        self.assertIsNone(src_file.meta_data)
        self.assertIsNotNone(src_file.geometry)
        self.assertIsNotNone(src_file.center_point)


class TestSourceFileManagerStoreFile(TestCase):

    def setUp(self):
        django.setup()

    @patch('storage.models.os.path.getsize')
    @patch('storage.models.os.mkdir')
    def test_success_new(self, mock_mkdir, mock_getsize):
        """Tests calling SourceFileManager.store_file() successfully with a new source file"""
        def new_getsize(path):
            return 100
        mock_getsize.side_effect = new_getsize

        workspace = storage_utils.create_workspace()
        remote_path = 'my/remote/path/file.txt'
        local_path = 'my/local/path/file.txt'
        workspace.upload_files = MagicMock()

        src_file = SourceFile.objects.store_file(local_path, [], workspace, remote_path)

        self.assertEqual('file.txt', src_file.file_name)
        self.assertEqual('3d8e577bddb17db339eae0b3d9bcf180', src_file.uuid)
        self.assertEqual(remote_path, src_file.file_path)
        self.assertEqual('text/plain', src_file.media_type)
        self.assertEqual(workspace.id, src_file.workspace_id)
