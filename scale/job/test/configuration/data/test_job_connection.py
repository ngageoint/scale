from __future__ import unicode_literals

import django
from django.test import TestCase

from job.configuration.data.exceptions import InvalidConnection
from job.configuration.data.job_connection import JobConnection
from job.configuration.interface.scale_file import ScaleFileDescription


class TestJobConnectionValidateInputFiles(TestCase):

    def setUp(self):
        django.setup()

    def test_required_missing(self):
        """Tests calling JobConnection.validate_input_files() when a required file parameter is missing"""

        files = {'Param1': (True, True, ScaleFileDescription()), 'Param2': (True, True, ScaleFileDescription())}

        conn = JobConnection()
        conn.add_input_file('Param1', True, None, False, False)

        self.assertRaises(InvalidConnection, conn.validate_input_files, files)
    
    def test_jamming_multiple_into_single(self):
        """Tests calling JobConnection.validate_input_files() when passing multiple files into a single file"""

        files = {'Param1': (True, False, ScaleFileDescription())}

        conn = JobConnection()
        conn.add_input_file('Param1', True, None, False, False)

        self.assertRaises(InvalidConnection, conn.validate_input_files, files)

    def test_bad_media_type(self):
        """Tests calling JobConnection.validate_input_files() with a bad media type"""

        file_desc = ScaleFileDescription()
        file_desc.add_allowed_media_type('application/json')
        files = {'Param1': (True, True, file_desc)}

        conn = JobConnection()
        conn.add_input_file('Param1', True, None, False, False)

        warnings = conn.validate_input_files(files)
        self.assertTrue(warnings)

    def test_optional_and_required(self):
        """Tests calling JobConnection.validate_input_files() when the connection has optional data for required input"""

        files = {'Param1': (True, True, ScaleFileDescription())}

        conn = JobConnection()
        conn.add_input_file('Param1', True, None, True, False)

        self.assertRaises(InvalidConnection, conn.validate_input_files, files)

    def test_successful(self):
        """Tests calling JobConnection.validate_input_files() successfully"""

        file_desc = ScaleFileDescription()
        file_desc.add_allowed_media_type('application/json')
        file_desc_2 = ScaleFileDescription()
        file_desc_2.add_allowed_media_type('application/json')
        file_desc_2.add_allowed_media_type('text/plain')
        files = {'Param1': (True, True, file_desc), 'Param2': (True, False, ScaleFileDescription()),
                 'Param3': (False, True, file_desc_2), 'Param4': (False, True, file_desc_2)}

        conn = JobConnection()
        conn.add_input_file('Param1', True, ['application/json'], False, False)
        conn.add_input_file('Param2', False, ['text/plain'], False, False)
        conn.add_input_file('Param3', False, ['text/plain'], False, False)

        # No exception is success
        warnings = conn.validate_input_files(files)
        self.assertFalse(warnings)


class TestJobConnectionValidateProperties(TestCase):

    def setUp(self):
        django.setup()

    def test_required_missing(self):
        """Tests calling JobConnection.validate_properties() when a required property is missing"""

        property_names = {'Param1': True, 'Param2': True, 'Param3': False}

        conn = JobConnection()
        conn.add_property('Param1')

        self.assertRaises(InvalidConnection, conn.validate_properties, property_names)

    def test_successful(self):
        """Tests calling JobConnection.validate_properties() successfully"""

        property_names = {'Param1': True, 'Param2': False, 'Param3': False}
        
        conn = JobConnection()
        conn.add_property('Param1')
        conn.add_property('Param2')
        
        # No exception is success
        warnings = conn.validate_properties(property_names)
        self.assertFalse(warnings)
