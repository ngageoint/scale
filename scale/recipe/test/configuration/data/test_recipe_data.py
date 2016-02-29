#@PydevCodeAnalysisIgnore

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
        '''Tests calling RecipeData.add_input_to_data() successfully with a file parameter'''

        recipe_input_name = u'foo'
        file_id = 1337
        job_input_name = u'bar'

        recipe_data = RecipeData({u'input_data': [{u'name': recipe_input_name, u'file_id': file_id}]})
        job_data = MagicMock()
        
        recipe_data.add_input_to_data(recipe_input_name, job_data, job_input_name)
        job_data.add_file_input.assert_called_with(job_input_name, file_id)

    def test_successful_file_list(self):
        '''Tests calling RecipeData.add_input_to_data() successfully with a file list parameter'''

        recipe_input_name = u'foo'
        file_ids = [1, 2, 3, 4]
        job_input_name = u'bar'

        recipe_data = RecipeData({u'input_data': [{u'name': recipe_input_name, u'file_ids': file_ids}]})
        job_data = MagicMock()
        
        recipe_data.add_input_to_data(recipe_input_name, job_data, job_input_name)
        job_data.add_file_list_input.assert_called_with(job_input_name, file_ids)

    def test_successful_property(self):
        '''Tests calling RecipeData.add_input_to_data() successfully with a property parameter'''

        recipe_input_name = u'foo'
        value = u'Doctor Who?'
        job_input_name = u'bar'

        recipe_data = RecipeData({u'input_data': [{u'name': recipe_input_name, u'value': value}]})
        job_data = MagicMock()
        
        recipe_data.add_input_to_data(recipe_input_name, job_data, job_input_name)
        job_data.add_property_input.assert_called_with(job_input_name, value)


class TestRecipeDataInit(TestCase):

    def setUp(self):
        django.setup()

    def test_init_blank(self):
        '''Tests calling RecipeData constructor with blank JSON.'''

        # No exception is success
        RecipeData({})

    def test_init_bad_version(self):
        '''Tests calling RecipeData constructor with bad version number.'''

        data = {u'version': u'BAD VERSION'}
        self.assertRaises(InvalidRecipeData, RecipeData, data)

    def test_init_no_input_name(self):
        '''Tests calling RecipeData constructor with missing data input name.'''

        data = {u'input_data': [{u'value': u'1'}]}
        self.assertRaises(InvalidRecipeData, RecipeData, data)

    def test_init_duplicate_input_name(self):
        '''Tests calling RecipeData constructor with duplicate data input name.'''

        data = {u'input_data': [{u'name': u'My Name', u'value': u'1'},
                                {u'name': u'My Name', u'value': u'1'}]}
        self.assertRaises(InvalidRecipeData, RecipeData, data)

    def test_init_workspace_id_not_integer(self):
        '''Tests calling RecipeData constructor with a non-integral value for workspace_id'''

        data = {u'workspace_id': u'foo'}
        self.assertRaises(InvalidRecipeData, RecipeData, data)

    def test_init_successful_one_property(self):
        '''Tests calling RecipeData constructor successfully with a single property input.'''

        data = {u'input_data': [{u'name': u'My Name', u'value': u'1'}]}

        # No exception is success
        RecipeData(data)


class TestRecipeDataValidateInputFiles(TestCase):

    def setUp(self):
        django.setup()

        self.file_1 = storage_utils.create_file(u'my_json_file.json', u'application/json')
        self.file_2 = storage_utils.create_file(u'my_text_file_1.txt', u'text/plain')
        self.file_3 = storage_utils.create_file(u'my_text_file_2.txt', u'text/plain')

    def test_missing_required(self):
        '''Tests calling RecipeData.validate_input_files() when a file is required, but missing'''

        data = {u'input_data': []}
        files = {u'File1': (True, True, ScaleFileDescription())}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_input_files, files)
    
    def test_not_required(self):
        '''Tests calling RecipeData.validate_input_files() when a file is missing, but required'''

        data = {u'input_data': []}
        files = {u'File1': (False, True, ScaleFileDescription())}
        # No exception is success
        warnings = RecipeData(data).validate_input_files(files)
        self.assertFalse(warnings)

    def test_multiple_missing_file_ids(self):
        '''Tests calling RecipeData.validate_input_files() with a multiple file param missing the file_ids field'''

        data = {u'input_data': [{u'name': u'File1'}]}
        files = {u'File1': (True, True, ScaleFileDescription())}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_input_files, files)

    def test_multiple_non_list(self):
        '''Tests calling RecipeData.validate_input_files() with a multiple file param with a non-list for file_ids field'''

        data = {u'input_data': [{u'name': u'File1', u'file_ids': u'STRING'}]}
        files = {u'File1': (True, True, ScaleFileDescription())}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_input_files, files)

    def test_multiple_non_integrals(self):
        '''Tests calling RecipeData.validate_input_files() with a multiple file param with a list of non-integrals for file_ids field'''

        data = {u'input_data': [{u'name': u'File1', u'file_ids': [123, u'STRING']}]}
        files = {u'File1': (True, True, ScaleFileDescription())}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_input_files, files)

    def test_multiple_given_single(self):
        '''Tests calling RecipeData.validate_input_files() with a multiple file param that is provided with a single file ID'''

        data = {u'input_data': [{u'name': u'File1', u'file_id': self.file_1.id}]}
        files = {u'File1': (True, True, ScaleFileDescription())}
        # No exception is success
        warnings = RecipeData(data).validate_input_files(files)
        self.assertFalse(warnings)

    def test_single_missing_file_id(self):
        '''Tests calling RecipeData.validate_input_files() with a single file param missing the file_id field'''

        data = {u'input_data': [{u'name': u'File1'}]}
        files = {u'File1': (True, False, ScaleFileDescription())}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_input_files, files)

    def test_single_non_integral(self):
        '''Tests calling RecipeData.validate_input_files() with a single file param with a non-integral for file_id field'''

        data = {u'input_data': [{u'name': u'File1', u'file_id': 'STRING'}]}
        files = {u'File1': (True, False, ScaleFileDescription())}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_input_files, files)
    
    def test_bad_media_type(self):
        '''Tests calling RecipeData.validate_input_files() with a file that has an invalid media type'''

        data = {u'input_data': [{u'name': u'File1', u'file_id': self.file_1.id}]}
        file_desc_1 = ScaleFileDescription()
        file_desc_1.add_allowed_media_type(u'text/plain')
        files = {u'File1': (True, False, file_desc_1)}
        warnings = RecipeData(data).validate_input_files(files)
        self.assertTrue(warnings)

    def test_bad_file_id(self):
        '''Tests calling RecipeData.validate_input_files() with a file that has an invalid ID'''

        data = {u'input_data': [{u'name': u'File1', u'file_id': 999999}]}
        files = {u'File1': (True, False, ScaleFileDescription())}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_input_files, files)

    def test_successful(self):
        '''Tests calling RecipeData.validate_input_files() with a valid set of job data'''

        data = {u'input_data': [{u'name': u'File1', u'file_id': self.file_1.id},
                                {u'name': u'File3', u'file_ids': [self.file_2.id]}]}
        file_desc_1 = ScaleFileDescription()
        file_desc_1.add_allowed_media_type(u'application/json')
        file_desc_3 = ScaleFileDescription()
        file_desc_3.add_allowed_media_type(u'text/plain')
        files = {u'File1': (True, False, file_desc_1),
                 u'File3': (True, True, file_desc_3)}
        # No exception is success
        warnings = RecipeData(data).validate_input_files(files)
        self.assertFalse(warnings)


class TestRecipeDataValidateProperties(TestCase):

    def setUp(self):
        django.setup()

    def test_missing_value(self):
        '''Tests calling RecipeData.validate_properties() when a property is missing a value'''

        data = {u'input_data': [{u'name': u'Param1'}]}
        properties = {u'Param1': False}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_properties, properties)

    def test_value_not_string(self):
        '''Tests calling RecipeData.validate_properties() when a property has a non-string value'''

        data = {u'input_data': [{u'name': u'Param1', u'value': 123}]}
        properties = {u'Param1': False}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_properties, properties)

    def test_missing_required(self):
        '''Tests calling RecipeData.validate_properties() when a property is required, but missing'''

        data = {u'input_data': []}
        properties = {u'Param1': True}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_properties, properties)

    def test_not_required(self):
        '''Tests calling RecipeData.validate_properties() when a property is missing, but is not required'''

        data = {u'input_data': []}
        properties = {u'Param1': False}
        # No exception is success
        warnings = RecipeData(data).validate_properties(properties)
        self.assertFalse(warnings)

    def test_required_successful(self):
        '''Tests calling RecipeData.validate_properties() successfully with a required property'''

        data = {u'input_data': [{u'name': u'Param1', u'value': u'Value1'}]}
        properties = {u'Param1': True}
        # No exception is success
        warnings = RecipeData(data).validate_properties(properties)
        self.assertFalse(warnings)


class TestRecipeDataValidateWorkspace(TestCase):

    def setUp(self):
        django.setup()
    
    @patch('recipe.configuration.data.recipe_data.DATA_FILE_STORE', new_callable=lambda: {u'DATA_FILE_STORE': DummyDataFileStore()})
    def test_missing_workspace_id(self, mock_store):
        '''Tests calling RecipeData.validate_workspace() when missing the workspace_id field'''

        data = {}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_workspace)

    @patch('recipe.configuration.data.recipe_data.DATA_FILE_STORE', new_callable=lambda: {u'DATA_FILE_STORE': DummyDataFileStore()})
    def test_workspace_not_exist(self, mock_store):
        '''Tests calling RecipeData.validate_workspace() with a workspace that does not exist'''

        data = {u'workspace_id': 2}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_workspace)

    @patch('recipe.configuration.data.recipe_data.DATA_FILE_STORE', new_callable=lambda: {u'DATA_FILE_STORE': DummyDataFileStore()})
    def test_workspace_not_active(self, mock_store):
        '''Tests calling RecipeData.validate_workspace() with a workspace that is not active'''

        data = {u'workspace_id': 3}
        self.assertRaises(InvalidRecipeData, RecipeData(data).validate_workspace)

    @patch('recipe.configuration.data.recipe_data.DATA_FILE_STORE', new_callable=lambda: {u'DATA_FILE_STORE': DummyDataFileStore()})
    def test_successful(self, mock_store):
        '''Tests calling RecipeData.validate_workspace() with successful data'''

        data = {u'workspace_id': 1}
        # No exception is success
        warnings = RecipeData(data).validate_workspace()
        self.assertFalse(warnings)
