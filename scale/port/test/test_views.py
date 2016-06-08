from __future__ import unicode_literals

import json

import django
from django.test.testcases import TestCase
from rest_framework import status

import error.test.utils as error_test_utils
import job.test.utils as job_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
import trigger.test.utils as trigger_test_utils
from error.models import Error
from job.models import JobType
from recipe.models import RecipeType


class TestConfigurationViewExport(TestCase):
    """Tests related to the configuration export endpoint"""

    def setUp(self):
        django.setup()

        self.recipe_type1 = recipe_test_utils.create_recipe_type()
        self.job_type1 = job_test_utils.create_job_type()
        self.error1 = error_test_utils.create_error(category='DATA')

    def test_errors(self):
        """Tests exporting only errors."""
        url = '/configuration/?include=errors'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(results['version'])
        self.assertEqual(len(results['recipe_types']), 0)
        self.assertEqual(len(results['job_types']), 0)
        self.assertEqual(len(results['errors']), 1)
        self.assertEqual(results['errors'][0]['name'], self.error1.name)

    def test_errors_system(self):
        """Tests exporting errors without any system-level entries."""
        error_test_utils.create_error(category='SYSTEM')

        url = '/configuration/'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results['errors']), 1)

    def test_errors_by_id(self):
        """Tests exporting errors by id."""
        error2 = error_test_utils.create_error(category='DATA')
        error3 = error_test_utils.create_error(category='DATA')

        url = '/configuration/?error_id=%s&error_id=%s' % (error2.id, error3.id)
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results['errors']), 2)

    def test_errors_by_name(self):
        """Tests exporting errors by name."""
        error2 = error_test_utils.create_error(category='DATA')
        error3 = error_test_utils.create_error(category='DATA')

        url = '/configuration/?error_name=%s&error_name=%s' % (error2.name, error3.name)
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results['errors']), 2)

    def test_job_types(self):
        """Tests exporting only job types."""
        url = '/configuration/?include=job_types'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(results['version'])
        self.assertEqual(len(results['recipe_types']), 0)
        self.assertEqual(len(results['job_types']), 1)
        self.assertEqual(results['job_types'][0]['name'], self.job_type1.name)
        self.assertEqual(len(results['errors']), 0)

    def test_job_types_system(self):
        """Tests exporting job types without any system-level entries."""
        job_test_utils.create_job_type(category='system')

        url = '/configuration/'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results['job_types']), 1)

    def test_job_types_by_id(self):
        """Tests exporting job types by id."""
        job_type2 = job_test_utils.create_job_type()
        job_type3 = job_test_utils.create_job_type()

        url = '/configuration/?job_type_id=%s&job_type_id=%s' % (job_type2.id, job_type3.id)
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results['job_types']), 2)

    def test_job_types_by_name(self):
        """Tests exporting job types by name."""
        job_test_utils.create_job_type(name='job-name')
        job_test_utils.create_job_type(name='job-name')

        url = '/configuration/?job_type_name=job-name'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results['job_types']), 2)

    def test_job_types_by_category(self):
        """Tests exporting job types by category."""
        job_test_utils.create_job_type(category='job-category')
        job_test_utils.create_job_type(category='job-category')

        url = '/configuration/?job_type_category=job-category'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results['job_types']), 2)

    def test_recipe_types(self):
        """Tests exporting only recipe types."""
        url = '/configuration/?include=recipe_types'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(results['version'])
        self.assertEqual(len(results['recipe_types']), 1)
        self.assertEqual(results['recipe_types'][0]['name'], self.recipe_type1.name)
        self.assertEqual(len(results['job_types']), 0)
        self.assertEqual(len(results['errors']), 0)

    def test_recipe_types_by_id(self):
        """Tests exporting recipe types by id."""
        recipe_type2 = recipe_test_utils.create_recipe_type()
        recipe_type3 = recipe_test_utils.create_recipe_type()

        url = '/configuration/?recipe_type_id=%s&recipe_type_id=%s' % (recipe_type2.id, recipe_type3.id)
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results['recipe_types']), 2)

    def test_recipe_types_by_name(self):
        """Tests exporting recipe types by name."""
        recipe_test_utils.create_recipe_type(name='recipe-name')
        recipe_test_utils.create_recipe_type(name='recipe-name')

        url = '/configuration/?recipe_type_name=recipe-name'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results['recipe_types']), 2)

    def test_all(self):
        """Tests exporting all the relevant models."""
        url = '/configuration/'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(results['version'])
        self.assertEqual(len(results['recipe_types']), 1)
        self.assertEqual(results['recipe_types'][0]['name'], self.recipe_type1.name)
        self.assertEqual(len(results['job_types']), 1)
        self.assertEqual(results['job_types'][0]['name'], self.job_type1.name)
        self.assertEqual(len(results['errors']), 1)
        self.assertEqual(results['errors'][0]['name'], self.error1.name)

    def test_cascaded_filters(self):
        """Tests exporting using a filter for recipes that is passed along to children filters."""
        error2 = error_test_utils.create_error(category='DATA')
        error_mapping2 = {
            'version': '1.0',
            'exit_codes': {
                '1': error2.name,
            },
        }
        job_type2 = job_test_utils.create_job_type(category='job-category', error_mapping=error_mapping2)

        recipe_definition = {
            'jobs': [{
                'name': 'job2',
                'job_type': {
                    'name': job_type2.name,
                    'version': job_type2.version,
                },
            }],
        }
        recipe_type2 = recipe_test_utils.create_recipe_type(definition=recipe_definition)

        url = '/configuration/?recipe_type_name=%s' % recipe_type2.name
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results['recipe_types']), 1)
        self.assertEqual(results['recipe_types'][0]['name'], recipe_type2.name)
        self.assertEqual(len(results['job_types']), 1)
        self.assertEqual(results['job_types'][0]['name'], job_type2.name)
        self.assertEqual(len(results['errors']), 1)
        self.assertEqual(results['errors'][0]['name'], error2.name)

    def test_combined_filters(self):
        """Tests exporting using multiple filters together."""
        error2 = error_test_utils.create_error(category='DATA')
        error_mapping2 = {
            'version': '1.0',
            'exit_codes': {
                '1': error2.name,
            },
        }
        job_type2 = job_test_utils.create_job_type(category='job-category', error_mapping=error_mapping2)

        error3 = error_test_utils.create_error(category='DATA')
        error_mapping3 = {
            'version': '1.0',
            'exit_codes': {
                '1': error3.name,
            },
        }
        job_type3 = job_test_utils.create_job_type(category='job-category', error_mapping=error_mapping3)

        recipe_definition = {
            'jobs': [{
                'name': 'job2',
                'job_type': {
                    'name': job_type2.name,
                    'version': job_type2.version,
                },
            }, {
                'name': 'job3',
                'job_type': {
                    'name': job_type3.name,
                    'version': job_type3.version,
                },
            }],
        }
        recipe_type2 = recipe_test_utils.create_recipe_type(definition=recipe_definition)

        url = '/configuration/?recipe_type_name=%s&job_type_name=%s&error_name=%s' % (recipe_type2.name, job_type2.name,
                                                                                      error2.name)
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results['recipe_types']), 1)
        self.assertEqual(results['recipe_types'][0]['name'], recipe_type2.name)
        self.assertEqual(len(results['job_types']), 1)
        self.assertEqual(results['job_types'][0]['name'], job_type2.name)
        self.assertEqual(len(results['errors']), 1)
        self.assertEqual(results['errors'][0]['name'], error2.name)


class TestConfigurationViewImport(TestCase):
    """Tests related to the configuration import endpoint"""

    def setUp(self):
        django.setup()

    def test_errors_create(self):
        """Tests importing only errors that create new models."""
        json_data = {
            'import': {
                'errors': [{
                    'name': 'test-name',
                    'title': 'test-title',
                    'description': 'test-description',
                    'category': 'DATA',
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        errors = Error.objects.filter(name='test-name')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(errors), 1)
        result = errors[0]

        self.assertEqual(result.title, 'test-title')
        self.assertEqual(result.description, 'test-description')
        self.assertEqual(result.category, 'DATA')

    def test_errors_edit(self):
        """Tests importing only errors that update existing models."""
        error = error_test_utils.create_error(category='DATA')
        json_data = {
            'import': {
                'errors': [{
                    'name': error.name,
                    'title': 'test-title EDIT',
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        errors = Error.objects.filter(name=error.name)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(errors), 1)
        result = errors[0]

        self.assertEqual(result.title, 'test-title EDIT')
        self.assertEqual(result.description, error.description)
        self.assertEqual(result.category, error.category)

    def test_errors_bad_system(self):
        """Tests rejecting a system category error."""
        json_data = {
            'import': {
                'errors': [{
                    'name': 'test-name',
                    'title': 'test-title',
                    'description': 'test-description',
                    'category': 'SYSTEM',
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        errors = Error.objects.all()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(errors), 0)

    def test_errors_bad_category(self):
        """Tests rejecting an error with an invalid category."""
        json_data = {
            'import': {
                'errors': [{
                    'name': 'test-name',
                    'title': 'test-title',
                    'description': 'test-description',
                    'category': 'test',
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        errors = Error.objects.all()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(errors), 0)

    def test_errors_bad_name(self):
        """Tests rejecting an error without a name."""
        json_data = {
            'import': {
                'errors': [{
                    'title': 'test-title',
                    'description': 'test-description',
                    'category': 'DATA',
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        errors = Error.objects.all()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(errors), 0)

    def test_errors_empty_fields(self):
        """Tests importing errors with empty string values for optional fields."""
        fields = ['description', 'title']
        error_type_dict = {
            'name': 'test-error',
            'category': 'DATA',
        }
        for field in fields:
            error_type_dict[field] = ''

        json_data = {
            'import': {
                'errors': [error_type_dict],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        errors = Error.objects.filter(name='test-error')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(len(errors), 1)
        result = errors[0]
        for field in fields:
            self.assertEqual(getattr(result, field), '')

    def test_errors_null_fields(self):
        """Tests importing errors with null values for optional fields."""
        fields = ['description', 'title']
        error_type_dict = {
            'name': 'test-error',
            'category': 'DATA',
        }
        for field in fields:
            error_type_dict[field] = None

        json_data = {
            'import': {
                'errors': [error_type_dict],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        errors = Error.objects.filter(name='test-error')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(len(errors), 1)
        result = errors[0]
        for field in fields:
            self.assertIsNone(getattr(result, field))

    def test_job_types_create(self):
        """Tests importing only job types that create new models."""
        error = error_test_utils.create_error()
        workspace = storage_test_utils.create_workspace()

        interface = {
            'version': '1.0',
            'command': 'test_cmd',
            'command_arguments': 'test_arg',
            'input_data': [],
            'output_data': [],
            'shared_resources': [],
        }
        error_mapping = {
            'version': '1.0',
            'exit_codes': {
                '1': error.name,
            },
        }

        trigger_rule_config = {
            'version': '1.0',
            'condition': {
                'media_type': 'text/plain',
                'data_types': [],
            },
            'data': {
                'input_data_name': 'input_file',
                'workspace_name': workspace.name,
            },
        }

        json_data = {
            'import': {
                'job_types': [{
                    'name': 'test-name',
                    'version': '1.0.0',
                    'title': 'test-title',
                    'description': 'test-description',
                    'category': 'test-category',
                    'author_name': 'test-author-name',
                    'author_url': 'test-author-url',
                    'is_operational': False,
                    'icon_code': 'test-icon-code',
                    'docker_privileged': True,
                    'docker_image': 'test-docker-image',
                    'priority': 1,
                    'timeout': 100,
                    'max_scheduled': 1,
                    'max_tries': 1,
                    'cpus_required': 2.0,
                    'mem_required': 1024.0,
                    'disk_out_const_required': 1024.0,
                    'disk_out_mult_required': 1.0,
                    'interface': interface,
                    'error_mapping': error_mapping,
                    'trigger_rule': {
                        'type': 'PARSE',
                        'name': 'test-name',
                        'is_active': False,
                        'configuration': trigger_rule_config,
                    },
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        job_types = JobType.objects.filter(name='test-name', version='1.0.0')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(job_types), 1)

        result = job_types[0]
        self.assertEqual(result.title, 'test-title')
        self.assertEqual(result.description, 'test-description')
        self.assertEqual(result.category, 'test-category')
        self.assertEqual(result.author_name, 'test-author-name')
        self.assertEqual(result.author_url, 'test-author-url')
        self.assertFalse(result.is_operational)
        self.assertEqual(result.icon_code, 'test-icon-code')
        self.assertTrue(result.docker_privileged)
        self.assertEqual(result.docker_image, 'test-docker-image')
        self.assertEqual(result.priority, 1)
        self.assertEqual(result.timeout, 100)
        self.assertEqual(result.max_scheduled, 1)
        self.assertEqual(result.max_tries, 1)
        self.assertEqual(result.cpus_required, 2.0)
        self.assertEqual(result.mem_required, 1024.0)
        self.assertEqual(result.disk_out_const_required, 1024.0)
        self.assertEqual(result.disk_out_mult_required, 1.0)

        self.assertDictEqual(result.interface, interface)
        self.assertDictEqual(result.error_mapping, error_mapping)

        self.assertIsNotNone(result.trigger_rule)
        self.assertEqual(result.trigger_rule.type, 'PARSE')
        self.assertEqual(result.trigger_rule.name, 'test-name')
        self.assertFalse(result.trigger_rule.is_active)
        self.assertDictEqual(result.trigger_rule.configuration, trigger_rule_config)

    def test_job_types_edit_simple(self):
        """Tests importing only job types that update basic models."""
        job_type = job_test_utils.create_job_type()
        json_data = {
            'import': {
                'job_types': [{
                    'name': job_type.name,
                    'version': job_type.version,
                    'title': 'test-title EDIT',
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        job_types = JobType.objects.filter(name=job_type.name, version=job_type.version)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(job_types), 1)
        result = job_types[0]

        self.assertEqual(result.title, 'test-title EDIT')
        self.assertEqual(result.description, job_type.description)
        self.assertIsNotNone(result.trigger_rule)

    def test_job_types_edit_interface(self):
        """Tests importing only job types that update the interface JSON."""
        job_type = job_test_utils.create_job_type()

        interface = {
            'version': '1.0',
            'command': 'test_cmd_edit',
            'command_arguments': 'test_arg_edit',
            'input_data': [],
            'output_data': [],
            'shared_resources': [],
        }

        json_data = {
            'import': {
                'job_types': [{
                    'name': job_type.name,
                    'version': job_type.version,
                    'interface': interface,
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        job_types = JobType.objects.filter(name=job_type.name, version=job_type.version)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(job_types), 1)
        result = job_types[0]

        self.assertEqual(result.title, job_type.title)
        self.assertDictEqual(result.interface, interface)

    def test_job_types_edit_error_mapping(self):
        """Tests importing only job types that update the error mapping JSON."""
        error = error_test_utils.create_error()
        job_type = job_test_utils.create_job_type()

        error_mapping = {
            'version': '1.0',
            'exit_codes': {
                '10': error.name,
            },
        }

        json_data = {
            'import': {
                'job_types': [{
                    'name': job_type.name,
                    'version': job_type.version,
                    'error_mapping': error_mapping,
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        job_types = JobType.objects.filter(name=job_type.name, version=job_type.version)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(job_types), 1)
        result = job_types[0]

        self.assertEqual(result.title, job_type.title)
        self.assertDictEqual(result.error_mapping, error_mapping)

    def test_job_types_edit_trigger_rule(self):
        """Tests importing only job types that update the trigger rule configuration JSON."""
        workspace = storage_test_utils.create_workspace()
        job_type = job_test_utils.create_job_type()

        trigger_rule_config = {
            'version': '1.0',
            'condition': {
                'media_type': 'image/jpg',
                'data_types': ['ABC'],
            },
            'data': {
                'input_data_name': 'input_file2',
                'workspace_name': workspace.name,
            },
        }

        json_data = {
            'import': {
                'job_types': [{
                    'name': job_type.name,
                    'version': job_type.version,
                    'trigger_rule': {
                        'type': 'INGEST',
                        'name': 'test-name2',
                        'is_active': False,
                        'configuration': trigger_rule_config,
                    },
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        job_types = JobType.objects.filter(name=job_type.name, version=job_type.version)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(job_types), 1)
        result = job_types[0]

        self.assertEqual(result.title, job_type.title)
        self.assertIsNotNone(result.trigger_rule)
        self.assertEqual(result.trigger_rule.type, 'INGEST')
        self.assertEqual(result.trigger_rule.name, 'test-name2')
        self.assertFalse(result.trigger_rule.is_active)
        self.assertDictEqual(result.trigger_rule.configuration, trigger_rule_config)

    def test_job_types_remove_trigger_rule(self):
        """Tests importing only job types that remove the trigger rule."""
        trigger_rule = trigger_test_utils.create_trigger_rule()
        job_type = job_test_utils.create_job_type(trigger_rule=trigger_rule)

        json_data = {
            'import': {
                'job_types': [{
                    'name': job_type.name,
                    'version': job_type.version,
                    'trigger_rule': None,
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        job_types = JobType.objects.filter(name=job_type.name, version=job_type.version)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(job_types), 1)
        result = job_types[0]

        self.assertEqual(result.title, job_type.title)
        self.assertIsNone(result.trigger_rule)

    def test_job_types_bad_system(self):
        """Tests rejecting a system category job type."""
        job_type = job_test_utils.create_job_type(category='system')
        json_data = {
            'import': {
                'job_types': [{
                    'name': job_type.name,
                    'version': job_type.version,
                    'title': 'test-title EDIT',
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        job_types = JobType.objects.filter(name=job_type.name, version=job_type.version)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(job_types), 1)
        result = job_types[0]

        self.assertEqual(result.title, job_type.title)

    def test_job_types_bad_name(self):
        """Tests rejecting a job type without a name."""
        job_type = job_test_utils.create_job_type()
        json_data = {
            'import': {
                'job_types': [{
                    'version': job_type.version,
                    'title': 'test-title EDIT',
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        job_types = JobType.objects.filter(name=job_type.name, version=job_type.version)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(job_types), 1)
        result = job_types[0]

        self.assertEqual(result.title, job_type.title)

    def test_job_types_bad_field(self):
        """Tests rejecting changes to read-only job type fields."""
        job_type = job_test_utils.create_job_type()
        json_data = {
            'import': {
                'job_types': [{
                    'name': job_type.name,
                    'version': job_type.version,
                    'is_long_running': True,
                    'is_system': True,
                    'title': 'test-title EDIT',
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        job_types = JobType.objects.filter(name=job_type.name, version=job_type.version)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(job_types), 1)
        result = job_types[0]

        self.assertFalse(result.is_long_running)
        self.assertFalse(result.is_system)
        self.assertEqual(result.title, 'test-title EDIT')

    def test_job_types_bad_interface(self):
        """Tests rejecting a job type with invalid interface JSON."""
        job_type = job_test_utils.create_job_type()

        interface = {
            'BAD': 'test',
        }

        json_data = {
            'import': {
                'job_types': [{
                    'name': job_type.name,
                    'version': job_type.version,
                    'interface': interface,
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        job_types = JobType.objects.filter(name=job_type.name, version=job_type.version)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(job_types), 1)
        result = job_types[0]

        self.assertDictEqual(result.interface, job_type.interface)

    def test_job_types_bad_error_mapping(self):
        """Tests rejecting a job type with invalid error mapping JSON."""
        job_type = job_test_utils.create_job_type()

        error_mapping = {
            'version': '1.0',
            'exit_codes': 'BAD',
        }

        json_data = {
            'import': {
                'job_types': [{
                    'name': job_type.name,
                    'version': job_type.version,
                    'error_mapping': error_mapping,
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        job_types = JobType.objects.filter(name=job_type.name, version=job_type.version)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(job_types), 1)
        result = job_types[0]

        self.assertDictEqual(result.error_mapping, job_type.error_mapping)

    def test_job_types_bad_trigger_rule(self):
        """Tests rejecting a job type with an invalid trigger rule."""
        job_type = job_test_utils.create_job_type()

        json_data = {
            'import': {
                'job_types': [{
                    'name': job_type.name,
                    'version': job_type.version,
                    'trigger_rule': {
                        'type': 'BAD',
                    },
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        job_types = JobType.objects.filter(name=job_type.name, version=job_type.version)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(job_types), 1)
        result = job_types[0]

        self.assertEqual(result.trigger_rule.type, job_type.trigger_rule.type)

    def test_job_types_missing_error(self):
        """Tests rejecting a job type with missing error dependencies."""
        job_type = job_test_utils.create_job_type()

        error_mapping = {
            'version': '1.0',
            'exit_codes': {
                '1': 'missing-error',
            },
        }

        json_data = {
            'import': {
                'job_types': [{
                    'name': job_type.name,
                    'version': job_type.version,
                    'error_mapping': error_mapping,
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        job_types = JobType.objects.filter(name=job_type.name, version=job_type.version)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(job_types), 1)
        result = job_types[0]

        self.assertDictEqual(result.error_mapping, job_type.error_mapping)

    def test_job_types_empty_fields(self):
        """Tests importing job types with empty string values for optional fields."""
        fields = ['author_name', 'author_url', 'category', 'description', 'docker_image', 'icon_code', 'title']
        job_type_dict = {
            'name': 'test-job',
            'version': '1.0.0',
            'interface': {
                'version': '1.0',
                'command': 'test_cmd',
                'command_arguments': 'test_arg',
                'input_data': [],
                'output_data': [],
                'shared_resources': [],
            },
        }
        for field in fields:
            job_type_dict[field] = ''

        json_data = {
            'import': {
                'job_types': [job_type_dict],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        job_types = JobType.objects.filter(name='test-job', version='1.0.0')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(len(job_types), 1)
        result = job_types[0]
        for field in fields:
            self.assertEqual(getattr(result, field), '')

    def test_job_types_null_fields(self):
        """Tests importing job types with null values for optional fields."""
        fields = ['author_name', 'author_url', 'category', 'description', 'docker_image', 'icon_code', 'max_scheduled',
                  'title', 'trigger_rule']
        job_type_dict = {
            'name': 'test-job',
            'version': '1.0.0',
            'interface': {
                'version': '1.0',
                'command': 'test_cmd',
                'command_arguments': 'test_arg',
                'input_data': [],
                'output_data': [],
                'shared_resources': [],
            },
        }
        for field in fields:
            job_type_dict[field] = None

        json_data = {
            'import': {
                'job_types': [job_type_dict],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        job_types = JobType.objects.filter(name='test-job', version='1.0.0')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(len(job_types), 1)
        result = job_types[0]
        for field in fields:
            self.assertIsNone(getattr(result, field))

    def test_recipe_types_create(self):
        """Tests importing only recipe types that create new models."""
        job_type = job_test_utils.create_job_type()
        workspace = storage_test_utils.create_workspace()

        definition = {
            'version': '1.0',
            'input_data': [{
                'type': 'file',
                'name': 'input_file',
                'required': True,
                'media_types': [
                    'text/plain',
                ],
            }],
            'jobs': [{
                'name': 'test-name',
                'job_type': {
                    'name': job_type.name,
                    'version': job_type.version,
                },
                'recipe_inputs': [{
                    'job_input': 'input_file',
                    'recipe_input': 'input_file',
                }],
                'dependencies': [],
            }],
        }

        trigger_rule_config = {
            'version': '1.0',
            'condition': {
                'media_type': 'text/plain',
                'data_types': [],
            },
            'data': {
                'input_data_name': 'input_file',
                'workspace_name': workspace.name,
            },
        }

        json_data = {
            'import': {
                'recipe_types': [{
                    'name': 'test-name',
                    'version': '1.0.0',
                    'title': 'test-title',
                    'description': 'test-description',
                    'definition': definition,
                    'trigger_rule': {
                        'type': 'PARSE',
                        'name': 'test-name',
                        'is_active': False,
                        'configuration': trigger_rule_config,
                    },
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        recipe_types = RecipeType.objects.filter(name='test-name', version='1.0.0')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(len(recipe_types), 1)

        result = recipe_types[0]
        self.assertEqual(result.title, 'test-title')
        self.assertEqual(result.description, 'test-description')
        self.assertDictEqual(result.definition, definition)

        self.assertIsNotNone(result.trigger_rule)
        self.assertEqual(result.trigger_rule.type, 'PARSE')
        self.assertEqual(result.trigger_rule.name, 'test-name')
        self.assertFalse(result.trigger_rule.is_active)
        self.assertDictEqual(result.trigger_rule.configuration, trigger_rule_config)

    def test_recipe_types_edit_simple(self):
        """Tests importing only recipe types that update basic models."""
        recipe_type = recipe_test_utils.create_recipe_type()
        json_data = {
            'import': {
                'recipe_types': [{
                    'name': recipe_type.name,
                    'version': recipe_type.version,
                    'title': 'test-title EDIT',
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        recipe_types = RecipeType.objects.filter(name=recipe_type.name, version=recipe_type.version)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(recipe_types), 1)
        result = recipe_types[0]

        self.assertEqual(result.title, 'test-title EDIT')
        self.assertEqual(result.description, recipe_type.description)
        self.assertIsNotNone(result.trigger_rule)

    def test_recipe_types_edit_definition(self):
        """Tests importing only recipe types that update the definition JSON."""
        job_type = job_test_utils.create_job_type()
        recipe_type = recipe_test_utils.create_recipe_type()

        definition = {
            'version': '1.0',
            'input_data': [{
                'type': 'file',
                'name': 'input_file2',
                'required': False,
                'media_types': [
                    'image/jpg',
                ],
            }],
            'jobs': [{
                'name': 'test-name2',
                'job_type': {
                    'name': job_type.name,
                    'version': job_type.version,
                },
                'recipe_inputs': [{
                    'job_input': 'input_file',
                    'recipe_input': 'input_file2',
                }],
                'dependencies': [],
            }],
        }

        json_data = {
            'import': {
                'recipe_types': [{
                    'name': recipe_type.name,
                    'version': recipe_type.version,
                    'definition': definition,
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        recipe_types = RecipeType.objects.filter(name=recipe_type.name, version=recipe_type.version)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(recipe_types), 1)
        result = recipe_types[0]

        self.assertEqual(result.title, recipe_type.title)
        self.assertDictEqual(result.definition, definition)

    def test_recipe_types_edit_trigger_rule(self):
        """Tests importing only recipe types that update the trigger rule configuration JSON."""
        workspace = storage_test_utils.create_workspace()
        recipe_type = recipe_test_utils.create_recipe_type()

        trigger_rule_config = {
            'version': '1.0',
            'condition': {
                'media_type': 'image/jpg',
                'data_types': ['ABC'],
            },
            'data': {
                'input_data_name': 'input_file2',
                'workspace_name': workspace.name,
            },
        }

        json_data = {
            'import': {
                'recipe_types': [{
                    'name': recipe_type.name,
                    'version': recipe_type.version,
                    'trigger_rule': {
                        'type': 'PARSE',
                        'name': 'test-name2',
                        'is_active': False,
                        'configuration': trigger_rule_config,
                    },
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        recipe_types = RecipeType.objects.filter(name=recipe_type.name, version=recipe_type.version)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(recipe_types), 1)
        result = recipe_types[0]

        self.assertEqual(result.title, recipe_type.title)
        self.assertIsNotNone(result.trigger_rule)
        self.assertEqual(result.trigger_rule.type, 'PARSE')
        self.assertEqual(result.trigger_rule.name, 'test-name2')
        self.assertFalse(result.trigger_rule.is_active)
        self.assertDictEqual(result.trigger_rule.configuration, trigger_rule_config)

    def test_recipe_types_remove_trigger_rule(self):
        """Tests importing only recipe types that remove the trigger rule."""
        trigger_rule = trigger_test_utils.create_trigger_rule()
        recipe_type = recipe_test_utils.create_recipe_type(trigger_rule=trigger_rule)

        json_data = {
            'import': {
                'recipe_types': [{
                    'name': recipe_type.name,
                    'version': recipe_type.version,
                    'trigger_rule': None,
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        recipe_types = RecipeType.objects.filter(name=recipe_type.name, version=recipe_type.version)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(recipe_types), 1)
        result = recipe_types[0]

        self.assertEqual(result.title, recipe_type.title)
        self.assertIsNone(result.trigger_rule)

    def test_recipe_types_bad_name(self):
        """Tests rejecting a recipe type without a name."""
        recipe_type = recipe_test_utils.create_recipe_type()
        json_data = {
            'import': {
                'recipe_types': [{
                    'version': recipe_type.version,
                    'title': 'test-title EDIT',
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        recipe_types = RecipeType.objects.filter(name=recipe_type.name, version=recipe_type.version)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(recipe_types), 1)
        result = recipe_types[0]

        self.assertEqual(result.title, recipe_type.title)

    def test_recipe_types_bad_interface(self):
        """Tests rejecting a recipe type with invalid definition JSON."""
        recipe_type = recipe_test_utils.create_recipe_type()

        definition = {
            'BAD': 'test',
        }

        json_data = {
            'import': {
                'recipe_types': [{
                    'name': recipe_type.name,
                    'version': recipe_type.version,
                    'definition': definition,
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        recipe_types = RecipeType.objects.filter(name=recipe_type.name, version=recipe_type.version)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(recipe_types), 1)
        result = recipe_types[0]

        self.assertDictEqual(result.definition, recipe_type.definition)

    def test_recipe_types_bad_trigger_rule(self):
        """Tests rejecting a recipe type with an invalid trigger rule."""
        recipe_type = recipe_test_utils.create_recipe_type()

        json_data = {
            'import': {
                'recipe_types': [{
                    'name': recipe_type.name,
                    'version': recipe_type.version,
                    'trigger_rule': {
                        'type': 'BAD',
                    },
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        recipe_types = RecipeType.objects.filter(name=recipe_type.name, version=recipe_type.version)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(recipe_types), 1)
        result = recipe_types[0]

        self.assertEqual(result.trigger_rule.type, recipe_type.trigger_rule.type)

    def test_recipe_types_missing_job_type(self):
        """Tests rejecting a recipe type with missing job type dependencies."""
        recipe_type = recipe_test_utils.create_recipe_type()

        definition = {
            'version': '1.0',
            'input_data': [{
                'type': 'file',
                'name': 'input_file',
                'required': True,
                'media_types': [
                    'text/plain',
                ],
            }],
            'jobs': [{
                'name': 'test-name',
                'job_type': {
                    'name': 'missing-job-type',
                    'version': '1.0.0',
                },
                'recipe_inputs': [{
                    'job_input': 'input_file',
                    'recipe_input': 'input_file',
                }],
                'dependencies': [],
            }],
        }

        json_data = {
            'import': {
                'recipe_types': [{
                    'name': recipe_type.name,
                    'version': recipe_type.version,
                    'definition': definition,
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        recipe_types = RecipeType.objects.filter(name=recipe_type.name, version=recipe_type.version)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(recipe_types), 1)
        result = recipe_types[0]

        self.assertDictEqual(result.definition, recipe_type.definition)

    def test_recipe_types_empty_fields(self):
        """Tests importing recipe types with empty string values for optional fields."""
        fields = ['description', 'title']
        recipe_type_dict = {
            'name': 'test-recipe',
            'version': '1.0.0',
            'definition': {
                'version': '1.0',
                'input_data': [],
                'jobs': [],
            },
        }
        for field in fields:
            recipe_type_dict[field] = ''

        json_data = {
            'import': {
                'recipe_types': [recipe_type_dict],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        recipe_types = RecipeType.objects.filter(name='test-recipe', version='1.0.0')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(len(recipe_types), 1)
        result = recipe_types[0]
        for field in fields:
            self.assertEqual(getattr(result, field), '')

    def test_recipe_types_null_fields(self):
        """Tests importing recipe types with null values for optional fields."""
        fields = ['description', 'title']
        recipe_type_dict = {
            'name': 'test-recipe',
            'version': '1.0.0',
            'definition': {
                'version': '1.0',
                'input_data': [],
                'jobs': [],
            },
        }
        for field in fields:
            recipe_type_dict[field] = None

        json_data = {
            'import': {
                'recipe_types': [recipe_type_dict],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        recipe_types = RecipeType.objects.filter(name='test-recipe', version='1.0.0')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(len(recipe_types), 1)
        result = recipe_types[0]
        for field in fields:
            self.assertIsNone(getattr(result, field))

    def test_all_create(self):
        """Tests importing all types that create new models."""
        workspace = storage_test_utils.create_workspace()

        interface = {
            'version': '1.0',
            'command': 'test_cmd',
            'command_arguments': 'test_arg',
            'input_data': [],
            'output_data': [],
            'shared_resources': [],
        }

        error_mapping = {
            'version': '1.0',
            'exit_codes': {
                '1': 'test-error-name',
            },
        }

        trigger_rule_config = {
            'version': '1.0',
            'condition': {
                'media_type': 'text/plain',
                'data_types': [],
            },
            'data': {
                'input_data_name': 'input_file',
                'workspace_name': workspace.name,
            },
        }

        definition = {
            'version': '1.0',
            'input_data': [{
                'type': 'file',
                'name': 'input_file',
                'required': True,
                'media_types': [
                    'text/plain',
                ],
            }],
            'jobs': [{
                'name': 'test-job-name',
                'job_type': {
                    'name': 'test-job-name',
                    'version': '1.0.0',
                },
                'recipe_inputs': [{
                    'job_input': 'input_file',
                    'recipe_input': 'input_file',
                }],
                'dependencies': [],
            }],
        }

        json_data = {
            'import': {
                'errors': [{
                    'name': 'test-error-name',
                    'title': 'test-error-title',
                    'description': 'test-error-description',
                    'category': 'DATA',
                }],
                'job_types': [{
                    'name': 'test-job-name',
                    'version': '1.0.0',
                    'title': 'test-job-title',
                    'description': 'test-job-description',
                    'category': 'test-job-category',
                    'author_name': 'test-author-name',
                    'author_url': 'test-author-url',
                    'is_operational': False,
                    'icon_code': 'test-icon-code',
                    'docker_privileged': True,
                    'docker_image': 'test-docker-image',
                    'priority': 1,
                    'timeout': 100,
                    'max_tries': 1,
                    'cpus_required': 2.0,
                    'mem_required': 1024.0,
                    'disk_out_const_required': 1024.0,
                    'disk_out_mult_required': 1.0,
                    'interface': interface,
                    'error_mapping': error_mapping,
                    'trigger_rule': {
                        'type': 'PARSE',
                        'name': 'test-trigger-name',
                        'is_active': False,
                        'configuration': trigger_rule_config,
                    },
                }],
                'recipe_types': [{
                    'name': 'test-recipe-name',
                    'version': '1.0.0',
                    'title': 'test-recipe-title',
                    'description': 'test-recipe-description',
                    'definition': definition,
                    'trigger_rule': {
                        'type': 'PARSE',
                        'name': 'test-trigger-name',
                        'configuration': trigger_rule_config,
                    },
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        errors = Error.objects.filter(name='test-error-name')
        job_types = JobType.objects.filter(name='test-job-name', version='1.0.0')
        recipe_types = RecipeType.objects.filter(name='test-recipe-name', version='1.0.0')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(errors), 1)
        self.assertEqual(len(job_types), 1)
        self.assertEqual(len(recipe_types), 1)

        self.assertEqual(errors[0].title, 'test-error-title')

        self.assertEqual(job_types[0].title, 'test-job-title')
        self.assertDictEqual(job_types[0].interface, interface)
        self.assertIsNone(job_types[0].max_scheduled)
        self.assertDictEqual(job_types[0].error_mapping, error_mapping)
        self.assertIsNotNone(job_types[0].trigger_rule)

        self.assertEqual(recipe_types[0].title, 'test-recipe-title')
        self.assertDictEqual(recipe_types[0].definition, definition)
        self.assertIsNotNone(recipe_types[0].trigger_rule)

    def test_all_edit(self):
        """Tests importing all types that edit existing models."""
        error = error_test_utils.create_error(category='DATA')
        job_type = job_test_utils.create_job_type()
        recipe_type = recipe_test_utils.create_recipe_type()

        json_data = {
            'import': {
                'errors': [{
                    'name': error.name,
                    'title': 'test-error-title',
                }],
                'job_types': [{
                    'name': job_type.name,
                    'version': job_type.version,
                    'title': 'test-job-title',
                }],
                'recipe_types': [{
                    'name': recipe_type.name,
                    'version': recipe_type.version,
                    'title': 'test-recipe-title',
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        errors = Error.objects.filter(name=error.name)
        job_types = JobType.objects.filter(name=job_type.name, version=job_type.version)
        recipe_types = RecipeType.objects.filter(name=recipe_type.name, version=recipe_type.version)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(errors), 1)
        self.assertEqual(len(job_types), 1)
        self.assertEqual(len(recipe_types), 1)

        self.assertEqual(errors[0].title, 'test-error-title')

        self.assertEqual(job_types[0].title, 'test-job-title')
        self.assertDictEqual(job_types[0].interface, job_type.interface)
        self.assertDictEqual(job_types[0].error_mapping, job_type.error_mapping)
        self.assertIsNotNone(job_types[0].trigger_rule)

        self.assertEqual(recipe_types[0].title, 'test-recipe-title')
        self.assertDictEqual(recipe_types[0].definition, recipe_type.definition)
        self.assertIsNotNone(recipe_types[0].trigger_rule)

    def test_all_mixed(self):
        """Tests importing all types that create new models and edit existing models."""

        # Create a job type with one error
        error = error_test_utils.create_error(category='DATA')

        error_mapping = {
            'version': '1.0',
            'exit_codes': {
                '-1': error.name,
            },
        }
        job_type = job_test_utils.create_job_type(error_mapping=error_mapping)

        # Create a recipe type with one job type
        definition = {
            'version': '1.0',
            'input_data': [{
                'type': 'file',
                'name': 'input_file',
                'required': True,
                'media_types': [
                    'text/plain',
                ],
            }],
            'jobs': [{
                'name': job_type.name,
                'job_type': {
                    'name': job_type.name,
                    'version': job_type.version,
                },
                'recipe_inputs': [{
                    'job_input': 'input_file',
                    'recipe_input': 'input_file',
                }],
                'dependencies': [],
            }],
        }
        recipe_type = recipe_test_utils.create_recipe_type(definition=definition)

        # Add a new error to the existing job type
        error_mapping['exit_codes']['1'] = 'test-error-name'

        # Add a new job type to the existing recipe type
        definition['jobs'].append({
            'name': 'test-job-name',
            'job_type': {
                'name': 'test-job-name',
                'version': '1.0.0',
            },
            'recipe_inputs': [{
                'job_input': 'input_file',
                'recipe_input': 'input_file',
            }],
            'dependencies': [],
        })

        interface = {
            'version': '1.0',
            'command': 'test_cmd',
            'command_arguments': 'test_arg',
            'input_data': [],
            'output_data': [],
            'shared_resources': [],
        }

        json_data = {
            'import': {
                'errors': [{
                    'name': 'test-error-name',
                    'title': 'test-error-title',
                    'description': 'test-error-description',
                    'category': 'DATA',
                }],
                'job_types': [{
                    'name': job_type.name,
                    'version': job_type.version,
                    'error_mapping': error_mapping,
                }, {
                    'name': 'test-job-name',
                    'version': '1.0.0',
                    'title': 'test-job-title',
                    'description': 'test-job-description',
                    'category': 'test-job-category',
                    'author_name': 'test-author-name',
                    'author_url': 'test-author-url',
                    'is_operational': False,
                    'icon_code': 'test-icon-code',
                    'docker_privileged': True,
                    'docker_image': 'test-docker-image',
                    'priority': 1,
                    'timeout': 100,
                    'max_tries': 1,
                    'cpus_required': 2.0,
                    'mem_required': 1024.0,
                    'disk_out_const_required': 1024.0,
                    'disk_out_mult_required': 1.0,
                    'interface': interface,
                    'error_mapping': None,
                    'trigger_rule': None,
                }],
                'recipe_types': [{
                    'name': recipe_type.name,
                    'version': recipe_type.version,
                    'definition': definition,
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        errors = Error.objects.all()
        job_types = JobType.objects.all()
        recipe_types = RecipeType.objects.all()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(errors), 2)
        self.assertEqual(len(job_types), 2)
        self.assertEqual(len(recipe_types), 1)

        error_keys = {error.name for error in errors}
        self.assertSetEqual(error_keys, {error.name, 'test-error-name'})

        job_keys = {(job_type.name, job_type.version) for job_type in job_types}
        self.assertSetEqual(job_keys, {(job_type.name, job_type.version), ('test-job-name', '1.0.0')})

        self.assertDictEqual(recipe_types[0].definition, definition)
        self.assertIsNotNone(recipe_types[0].trigger_rule)

    def test_all_mixed_bad(self):
        """Tests importing all types that invalidates the models as the imports are applied."""

        # Create a job type with one error
        error = error_test_utils.create_error(category='DATA')

        error_mapping = {
            'version': '1.0',
            'exit_codes': {
                '-1': error.name,
            },
        }
        job_type = job_test_utils.create_job_type(error_mapping=error_mapping)

        # Create a recipe type with one job type
        definition = {
            'version': '1.0',
            'input_data': [{
                'type': 'file',
                'name': 'input_file',
                'required': True,
                'media_types': [
                    'text/plain',
                ],
            }],
            'jobs': [{
                'name': job_type.name,
                'job_type': {
                    'name': job_type.name,
                    'version': job_type.version,
                },
                'recipe_inputs': [{
                    'job_input': 'input_file',
                    'recipe_input': 'input_file',
                }],
                'dependencies': [],
            }],
        }
        recipe_type = recipe_test_utils.create_recipe_type(definition=definition)

        # Add a new error to the existing job type
        error_mapping['exit_codes']['1'] = 'test-error-name'

        # Add a new job type to the existing recipe type that is not defined
        definition['jobs'].append({
            'name': 'test-job-name',
            'job_type': {
                'name': 'test-job-name',
                'version': '1.0.0',
            },
            'recipe_inputs': [{
                'job_input': 'input_file',
                'recipe_input': 'input_file',
            }],
            'dependencies': [],
        })

        interface = {
            'version': '1.0',
            'command': 'test_cmd',
            'command_arguments': 'test_arg',
            'input_data': [],
            'output_data': [],
            'shared_resources': [],
        }

        json_data = {
            'import': {
                'errors': [{
                    'name': 'test-error-name',
                    'title': 'test-error-title',
                    'description': 'test-error-description',
                    'category': 'DATA',
                }],
                'job_types': [{
                    'name': job_type.name,
                    'version': job_type.version,
                    'error_mapping': error_mapping,
                    'interface': interface,
                }],
                'recipe_types': [{
                    'name': recipe_type.name,
                    'version': recipe_type.version,
                    'definition': definition,
                }],
            },
        }

        url = '/configuration/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        json.loads(response.content)

        errors = Error.objects.all()
        job_types = JobType.objects.all()
        recipe_types = RecipeType.objects.all()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(len(errors), 1)
        self.assertEqual(len(job_types), 1)
        self.assertEqual(len(recipe_types), 1)


class TestConfigurationDownloadView(TestCase):
    """Tests related to the configuration export download endpoint"""

    def setUp(self):
        django.setup()

        self.recipe_type1 = recipe_test_utils.create_recipe_type()
        self.job_type1 = job_test_utils.create_job_type()
        self.error1 = error_test_utils.create_error(category='DATA')

    def test_download(self):
        """Tests exporting as a separate download file."""
        url = '/configuration/download/'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.has_header('Content-Disposition'))
        self.assertEqual(len(results['recipe_types']), 1)
        self.assertEqual(len(results['job_types']), 1)
        self.assertEqual(len(results['errors']), 1)


class TestConfigurationUploadView(TestCase):
    """Tests related to the configuration import upload endpoint"""

    def setUp(self):
        django.setup()

    def test_upload_missing_file(self):
        """Tests importing as a separate upload file without any provided content."""

        url = '/configuration/upload/'
        response = self.client.generic('POST', url, '', 'multipart/form-data')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # TODO: Figure out to write a unit test for the success case


class TestConfigurationValidationView(TestCase):
    """Tests related to the configuration import endpoint"""

    def setUp(self):
        django.setup()

    def test_successful(self):
        """Tests validating an edit of all types successfully."""
        error = error_test_utils.create_error(category='DATA')
        job_type = job_test_utils.create_job_type()
        recipe_type = recipe_test_utils.create_recipe_type()

        json_data = {
            'import': {
                'errors': [{
                    'name': error.name,
                    'title': 'test-error-title',
                    'category': 'ALGORITHM',
                }],
                'job_types': [{
                    'name': job_type.name,
                    'version': job_type.version,
                    'title': 'test-job-title',
                }],
                'recipe_types': [{
                    'name': recipe_type.name,
                    'version': recipe_type.version,
                    'title': 'test-recipe-title',
                }],
            },
        }

        url = '/configuration/validation/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        results = json.loads(response.content)

        errors = Error.objects.filter(name=error.name)
        job_types = JobType.objects.filter(name=job_type.name, version=job_type.version)
        recipe_types = RecipeType.objects.filter(name=recipe_type.name, version=recipe_type.version)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(results, {'warnings': []})

        self.assertEqual(len(errors), 1)
        self.assertEqual(len(job_types), 1)
        self.assertEqual(len(recipe_types), 1)

        self.assertEqual(errors[0].title, error.title)
        self.assertEqual(job_types[0].title, job_type.title)
        self.assertEqual(recipe_types[0].title, recipe_type.title)

    def test_errors(self):
        """Tests validating an edit of all types with a critical error."""
        error = error_test_utils.create_error(category='SYSTEM')
        job_type = job_test_utils.create_job_type(category='system')
        recipe_type = recipe_test_utils.create_recipe_type()

        json_data = {
            'import': {
                'errors': [{
                    'name': error.name,
                    'title': 'test-error-title',
                }],
                'job_types': [{
                    'name': job_type.name,
                    'version': job_type.version,
                    'title': 'test-job-title',
                }],
                'recipe_types': [{
                    'name': recipe_type.name,
                    'version': recipe_type.version,
                    'title': 'test-recipe-title',
                }],
            },
        }

        url = '/configuration/validation/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        results = json.loads(response.content)

        errors = Error.objects.filter(name=error.name)
        job_types = JobType.objects.filter(name=job_type.name, version=job_type.version)
        recipe_types = RecipeType.objects.filter(name=recipe_type.name, version=recipe_type.version)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIsNotNone(results['detail'])

        self.assertEqual(len(errors), 1)
        self.assertEqual(len(job_types), 1)
        self.assertEqual(len(recipe_types), 1)

        self.assertEqual(errors[0].title, error.title)
        self.assertEqual(job_types[0].title, job_type.title)
        self.assertEqual(recipe_types[0].title, recipe_type.title)

    def test_warnings(self):
        """Tests validating an edit of all types with only warnings."""
        error = error_test_utils.create_error(category='DATA')
        job_type = job_test_utils.create_job_type()
        recipe_type = recipe_test_utils.create_recipe_type()

        json_data = {
            'import': {
                'errors': [{
                    'name': error.name,
                    'title': 'test-error-title',
                }],
                'job_types': [{
                    'name': job_type.name,
                    'version': job_type.version,
                    'title': 'test-job-title',
                    'is_long_running': True,
                }],
                'recipe_types': [{
                    'name': recipe_type.name,
                    'version': recipe_type.version,
                    'title': 'test-recipe-title',
                }],
            },
        }

        url = '/configuration/validation/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        results = json.loads(response.content)

        errors = Error.objects.filter(name=error.name)
        job_types = JobType.objects.filter(name=job_type.name, version=job_type.version)
        recipe_types = RecipeType.objects.filter(name=recipe_type.name, version=recipe_type.version)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results['warnings']), 1)

        self.assertEqual(len(errors), 1)
        self.assertEqual(len(job_types), 1)
        self.assertEqual(len(recipe_types), 1)

        self.assertEqual(errors[0].title, error.title)
        self.assertEqual(job_types[0].title, job_type.title)
        self.assertEqual(recipe_types[0].title, recipe_type.title)
