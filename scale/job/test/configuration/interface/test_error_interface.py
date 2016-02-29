#@PydevCodeAnalysisIgnore
from __future__ import unicode_literals

import django
from django.test import TestCase

import error.test.utils as error_test_utils
from error.models import Error
from job.configuration.interface.error_interface import ErrorInterface
from job.configuration.interface.exceptions import InvalidInterfaceDefinition


class TestErrorInterfaceValidate(TestCase):

    def setUp(self):
        django.setup()

        self.error_1 = error_test_utils.create_error(name='unknown', category='SYSTEM')
        self.error_2 = error_test_utils.create_error(name='database', category='SYSTEM')
        self.error_3 = error_test_utils.create_error(name='timeout', category='ALGORITHM')

    def test_get_error_zero(self):
        ''' Tests that no error is returned when the exit_code is 0'''

        error_interface_dict = {
            'version': '1.0',
            'exit_codes': {
                '1': self.error_1.name,
                '2': self.error_2.name,
                '3': self.error_3.name,
            },
        }

        error_interface = ErrorInterface(error_interface_dict)
        error = error_interface.get_error(0)

        self.assertIsNone(error)

    def test_get_error_found(self):
        ''' Tests that an error model is returned given an exit_code other than 0'''

        error_interface_dict = {
            'version': '1.0',
            'exit_codes': {
                '1': self.error_1.name,
                '2': self.error_2.name,
                '3': self.error_3.name,
            },
        }

        error_interface = ErrorInterface(error_interface_dict)
        error = error_interface.get_error(1)

        self.assertIsNotNone(error)
        self.assertEqual(error.name, Error.objects.get_unknown_error().name)

    def test_get_error_missing(self):
        ''' Tests that an unknown error is returned when a non-registered name is found in the mapping'''

        error_interface_dict = {
            'version': '1.0',
            'exit_codes': {
                '1': self.error_1.name,
                '2': self.error_2.name,
                '3': self.error_3.name,
            },
        }

        error_interface = ErrorInterface(error_interface_dict)
        error = error_interface.get_error(4)

        self.assertIsNotNone(error)
        self.assertEqual(error.name, Error.objects.get_unknown_error().name)

    def test_get_error_names(self):
        '''Tests getting error names from the mapping.'''

        error_interface_dict = {
            'version': '1.0',
            'exit_codes': {
                '1': self.error_1.name,
                '2': self.error_2.name,
            },
        }

        error_interface = ErrorInterface(error_interface_dict)

        error_names = error_interface.get_error_names()
        self.assertSetEqual(error_names, {self.error_1.name, self.error_2.name})

    def test_get_error_names_none(self):
        '''Tests getting error names when there is no error interface.'''

        error_interface_dict = {}

        error_interface = ErrorInterface(error_interface_dict)

        error_names = error_interface.get_error_names()
        self.assertSetEqual(error_names, set())

    def test_get_error_names_empty(self):
        '''Tests getting error names when there are no exit codes defined.'''

        error_interface_dict = {
            'version': '1.0',
            'exit_codes': {},
        }

        error_interface = ErrorInterface(error_interface_dict)

        error_names = error_interface.get_error_names()
        self.assertSetEqual(error_names, set())

    def test_get_error_names_unique(self):
        '''Tests getting error names without duplicates.'''

        error_interface_dict = {
            'version': '1.0',
            'exit_codes': {
                '0': self.error_1.name,
                '2': self.error_2.name,
                '5': self.error_1.name,
            },
        }

        error_interface = ErrorInterface(error_interface_dict)

        error_names = error_interface.get_error_names()
        self.assertSetEqual(error_names, {self.error_1.name, self.error_2.name})

    def test_validate_empty(self):
        '''Tests validating no error names.'''

        error_interface_dict = {
            'version': '1.0',
            'exit_codes': {
            },
        }

        error_interface = ErrorInterface(error_interface_dict)

        # No exception is passing
        error_interface.validate()

    def test_validate_success(self):
        '''Tests validating all error names.'''

        error_interface_dict = {
            'version': '1.0',
            'exit_codes': {
                '1': self.error_1.name,
                '2': self.error_2.name,
                '3': self.error_3.name,
            },
        }

        error_interface = ErrorInterface(error_interface_dict)

        # No exception is passing
        error_interface.validate()

    def test_validate_missing(self):
        '''Tests validating when some error names are missing.'''

        error_interface_dict = {
            'version': '1.0',
            'exit_codes': {
                '1': self.error_1.name,
                '4': 'test-missing-name',
            },
        }

        error_interface = ErrorInterface(error_interface_dict)

        self.assertRaises(InvalidInterfaceDefinition, error_interface.validate)
