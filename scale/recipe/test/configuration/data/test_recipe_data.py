from __future__ import unicode_literals

import django
from django.test import TestCase
from mock import MagicMock, patch

from job.configuration.data.data_file import AbstractDataFileStore
from job.configuration.interface.scale_file import ScaleFileDescription
from recipe.configuration.data.exceptions import InvalidRecipeData
from recipe.configuration.data.recipe_data import RecipeData
from storage.test import utils as storage_utils


class DummyDataFileStore(AbstractDataFileStore):

    def get_workspaces(self, workspace_ids):
        results = {}
        if 1 in workspace_ids:
            results[long(1)] = True
        if 3 in workspace_ids:
            results[long(3)] = False
        return results

    def store_files(self, files, input_file_ids, job_exe):
        pass


class TestRecipeDataAddInputToData(TestCase):

    def setUp(self):
        django.setup()

    def test_successful_file(self):
        """Tests calling RecipeData.add_input_to_data() successfully with a file parameter"""

        recipe_input_name = 'foo'
        file_id = 1337
        job_input_name = 'bar'

        recipe_data = RecipeData({'input_data': [{'name': recipe_input_name, 'file_id': file_id}]})
        job_data = MagicMock()
        
        recipe_data.add_input_to_data(recipe_input_name, job_data, job_input_name)
        job_data.add_file_input.assert_called_with(job_input_name, file_id)

    def test_successful_file_list(self):
        """Tests calling RecipeData.add_input_to_data() successfully with a file list parameter"""

        recipe_input_name = 'foo'
        file_ids = [1, 2, 3, 4]
        job_input_name = 'bar'

        recipe_data = RecipeData({'input_data': [{'name': recipe_input_name, 'file_ids': file_ids}]})
        job_data = MagicMock()
        
        recipe_data.add_input_to_data(recipe_input_name, job_data, job_input_name)
        job_data.add_file_list_input.assert_called_with(job_input_name, file_ids)

    def test_successful_property(self):
        """Tests calling RecipeData.add_input_to_data() successfully with a property parameter"""

        recipe_input_name = 'foo'
        value = 'Doctor Who?'
        job_input_name = 'bar'

        recipe_data = RecipeData({'input_data': [{'name': recipe_input_name, 'value': value}]})
        job_data = MagicMock()
        
        recipe_data.add_input_to_data(recipe_input_name, job_data, job_input_name)
        job_data.add_property_input.assert_called_with(job_input_name, value)


class TestRecipeDataInit(TestCase):

    def setUp(self):
        django.setup()

    def test_init_blank(self):
        """Tests calling RecipeData constructor with blank JSON."""

        # No exception is success
        RecipeData({})

    def test_init_bad_version(self):
        """Tests calling RecipeData constructor with bad version number."""

        data = {'version': 'BAD VERSION'}
        self.assertRaises(InvalidRecipeData, RecipeData, data)

    def test_init_no_input_name(self):
        """Tests calling RecipeData constructor with missing data input name."""

        data = {'input_data': [{'value': '1'}]}
        self.assertRaises(InvalidRecipeData, RecipeData, data)

    def test_init_duplicate_input_name(self):
        """Tests calling RecipeData constructor with duplicate data input name."""

        data = {'input_data': [{'name': 'My Name', 'value': '1'},
                                {'name': 'My Name', 'value': '1'}]}
        self.assertRaises(InvalidRecipeData, RecipeData, data)

    def test_init_workspace_id_not_integer(self):
        """Tests calling RecipeData constructor with a non-integral value for workspace_id"""

        data = {'workspace_id': 'foo'}
        self.assertRaises(InvalidRecipeData, RecipeData, data)

    def test_init_successful_one_property(self):
        """Tests calling RecipeData constructor successfully with a single property input."""

        data = {'input_data': [{'name': 'My Name', 'value': '1'}]}

        # No exception is success
        RecipeData(data)


class TestRecipeDataValidateInputFiles(TestCase):

    def setUp(self):
        django.setup()

        self.file_1 = storage_utils.create_file('my_json_file.json', 'application/json')
        self.file_2 = storage_utils.create_file('my_text_file_1.txt', 'text/plain')
        self.file_3 = storage_utils.create_file('my_text_file_2.txt', 'text/plain')

    def test_missing_required(self):
        """Tests calling RecipeData.validate_input_files() when a file is required, but missing"""

        data = {'input_data': []}
        files = {'File1': (True, True, ScaleFileDescription())}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_input_files, files)
    
    def test_not_required(self):
        """Tests calling RecipeData.validate_input_files() when a file is missing, but required"""

        data = {'input_data': []}
        files = {'File1': (False, True, ScaleFileDescription())}
        # No exception is success
        warnings = RecipeData(data).validate_input_files(files)
        self.assertFalse(warnings)

    def test_multiple_missing_file_ids(self):
        """Tests calling RecipeData.validate_input_files() with a multiple file param missing the file_ids field"""

        data = {'input_data': [{'name': 'File1'}]}
        files = {'File1': (True, True, ScaleFileDescription())}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_input_files, files)

    def test_multiple_non_list(self):
        """Tests calling RecipeData.validate_input_files() with a multiple file param with a non-list for file_ids field"""

        data = {'input_data': [{'name': 'File1', 'file_ids': 'STRING'}]}
        files = {'File1': (True, True, ScaleFileDescription())}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_input_files, files)

    def test_multiple_non_integrals(self):
        """Tests calling RecipeData.validate_input_files() with a multiple file param with a list of non-integrals for file_ids field"""

        data = {'input_data': [{'name': 'File1', 'file_ids': [123, 'STRING']}]}
        files = {'File1': (True, True, ScaleFileDescription())}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_input_files, files)

    def test_multiple_given_single(self):
        """Tests calling RecipeData.validate_input_files() with a multiple file param that is provided with a single file ID"""

        data = {'input_data': [{'name': 'File1', 'file_id': self.file_1.id}]}
        files = {'File1': (True, True, ScaleFileDescription())}
        # No exception is success
        warnings = RecipeData(data).validate_input_files(files)
        self.assertFalse(warnings)

    def test_single_missing_file_id(self):
        """Tests calling RecipeData.validate_input_files() with a single file param missing the file_id field"""

        data = {'input_data': [{'name': 'File1'}]}
        files = {'File1': (True, False, ScaleFileDescription())}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_input_files, files)

    def test_single_non_integral(self):
        """Tests calling RecipeData.validate_input_files() with a single file param with a non-integral for file_id field"""

        data = {'input_data': [{'name': 'File1', 'file_id': 'STRING'}]}
        files = {'File1': (True, False, ScaleFileDescription())}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_input_files, files)
    
    def test_bad_media_type(self):
        """Tests calling RecipeData.validate_input_files() with a file that has an invalid media type"""

        data = {'input_data': [{'name': 'File1', 'file_id': self.file_1.id}]}
        file_desc_1 = ScaleFileDescription()
        file_desc_1.add_allowed_media_type('text/plain')
        files = {'File1': (True, False, file_desc_1)}
        warnings = RecipeData(data).validate_input_files(files)
        self.assertTrue(warnings)

    def test_bad_file_id(self):
        """Tests calling RecipeData.validate_input_files() with a file that has an invalid ID"""

        data = {'input_data': [{'name': 'File1', 'file_id': 999999}]}
        files = {'File1': (True, False, ScaleFileDescription())}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_input_files, files)

    def test_successful(self):
        """Tests calling RecipeData.validate_input_files() with a valid set of job data"""

        data = {'input_data': [{'name': 'File1', 'file_id': self.file_1.id},
                                {'name': 'File3', 'file_ids': [self.file_2.id]}]}
        file_desc_1 = ScaleFileDescription()
        file_desc_1.add_allowed_media_type('application/json')
        file_desc_3 = ScaleFileDescription()
        file_desc_3.add_allowed_media_type('text/plain')
        files = {'File1': (True, False, file_desc_1),
                 'File3': (True, True, file_desc_3)}
        # No exception is success
        warnings = RecipeData(data).validate_input_files(files)
        self.assertFalse(warnings)


class TestRecipeDataValidateProperties(TestCase):

    def setUp(self):
        django.setup()

    def test_missing_value(self):
        """Tests calling RecipeData.validate_properties() when a property is missing a value"""

        data = {'input_data': [{'name': 'Param1'}]}
        properties = {'Param1': False}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_properties, properties)

    def test_value_not_string(self):
        """Tests calling RecipeData.validate_properties() when a property has a non-string value"""

        data = {'input_data': [{'name': 'Param1', 'value': 123}]}
        properties = {'Param1': False}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_properties, properties)

    def test_missing_required(self):
        """Tests calling RecipeData.validate_properties() when a property is required, but missing"""

        data = {'input_data': []}
        properties = {'Param1': True}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_properties, properties)

    def test_not_required(self):
        """Tests calling RecipeData.validate_properties() when a property is missing, but is not required"""

        data = {'input_data': []}
        properties = {'Param1': False}
        # No exception is success
        warnings = RecipeData(data).validate_properties(properties)
        self.assertFalse(warnings)

    def test_required_successful(self):
        """Tests calling RecipeData.validate_properties() successfully with a required property"""

        data = {'input_data': [{'name': 'Param1', 'value': 'Value1'}]}
        properties = {'Param1': True}
        # No exception is success
        warnings = RecipeData(data).validate_properties(properties)
        self.assertFalse(warnings)


class TestRecipeDataValidateWorkspace(TestCase):

    def setUp(self):
        django.setup()
    
    @patch('recipe.configuration.data.recipe_data.DATA_FILE_STORE', new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_missing_workspace_id(self, mock_store):
        """Tests calling RecipeData.validate_workspace() when missing the workspace_id field"""

        data = {}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_workspace)

    @patch('recipe.configuration.data.recipe_data.DATA_FILE_STORE', new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_workspace_not_exist(self, mock_store):
        """Tests calling RecipeData.validate_workspace() with a workspace that does not exist"""

        data = {'workspace_id': 2}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_workspace)

    @patch('recipe.configuration.data.recipe_data.DATA_FILE_STORE', new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_workspace_not_active(self, mock_store):
        """Tests calling RecipeData.validate_workspace() with a workspace that is not active"""

        data = {'workspace_id': 3}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_workspace)

    @patch('recipe.configuration.data.recipe_data.DATA_FILE_STORE', new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_successful(self, mock_store):
        """Tests calling RecipeData.validate_workspace() with successful data"""

        data = {'workspace_id': 1}
        # No exception is success
        warnings = RecipeData(data).validate_workspace()
        self.assertFalse(warnings)
