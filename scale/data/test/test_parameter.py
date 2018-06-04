from __future__ import unicode_literals

import django

from django.test.testcases import TestCase
from mock import MagicMock

from data.interface.exceptions import InvalidInterface, InvalidInterfaceConnection
from data.interface.interface import Interface
from data.interface.parameter import FileParameter, JsonParameter


class TestFileParameter(TestCase):
    """Tests related to the FileParameter class"""

    def setUp(self):
        django.setup()

    def test_validate_connection(self):
        """Tests calling FileParameter.validate_connection()"""

        file_param = FileParameter('input_1', ['application/json'])
        connecting_param = JsonParameter('input_1', 'array')

        # Invalid parameter type
        with self.assertRaises(InvalidInterfaceConnection) as context:
            file_param.validate_connection(connecting_param)
        self.assertEqual(context.exception.error.name, 'MISMATCHED_PARAM_TYPE')

        # Parameter is required
        connecting_param = FileParameter('input_1', ['application/json'], required=False)
        with self.assertRaises(InvalidInterfaceConnection) as context:
            file_param.validate_connection(connecting_param)
        self.assertEqual(context.exception.error.name, 'PARAM_REQUIRED')

        # Multiple files not accepted
        connecting_param = FileParameter('input_1', ['application/json'], multiple=True)
        with self.assertRaises(InvalidInterfaceConnection) as context:
            file_param.validate_connection(connecting_param)
        self.assertEqual(context.exception.error.name, 'NO_MULTIPLE_FILES')

        # Valid parameter connection
        connecting_param = FileParameter('input_1', ['application/json'])
        warnings = file_param.validate_connection(connecting_param)
        self.assertListEqual(warnings, [])

        # Multiple file parameter can accept single file parameter
        file_param = FileParameter('input_1', ['application/json'], multiple=True)
        connecting_param = FileParameter('input_1', ['application/json'])
        warnings = file_param.validate_connection(connecting_param)
        self.assertListEqual(warnings, [])

        # Mismatched media types
        file_param = FileParameter('input_1', ['application/json'])
        connecting_param = FileParameter('input_1', ['application/json', 'image/gif'])
        warnings = file_param.validate_connection(connecting_param)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0].name, 'MISMATCHED_MEDIA_TYPES')


class TestJsonParameter(TestCase):
    """Tests related to the JsonParameter class"""

    def setUp(self):
        django.setup()

    def test_validate(self):
        """Tests calling JsonParameter.validate()"""
        connecting_param = FileParameter('input_1', ['application/json'])

        # Invalid JSON type
        json_param = JsonParameter('input_1', 'BAD')
        with self.assertRaises(InvalidInterface) as context:
            json_param.validate()
        self.assertEqual(context.exception.error.name, 'INVALID_JSON_TYPE')

        # Valid JSON parameter
        json_param = JsonParameter('input_1', 'string')
        warnings = json_param.validate()
        self.assertListEqual(warnings, [])

    def test_validate_connection(self):
        """Tests calling JsonParameter.validate_connection()"""

        json_param = JsonParameter('input_1', 'string')
        connecting_param = FileParameter('input_1', ['application/json'])

        # Invalid parameter type
        with self.assertRaises(InvalidInterfaceConnection) as context:
            json_param.validate_connection(connecting_param)
        self.assertEqual(context.exception.error.name, 'MISMATCHED_PARAM_TYPE')

        # Parameter is required
        connecting_param = JsonParameter('input_1', 'string', required=False)
        with self.assertRaises(InvalidInterfaceConnection) as context:
            json_param.validate_connection(connecting_param)
        self.assertEqual(context.exception.error.name, 'PARAM_REQUIRED')

        # Mismatched JSON type
        connecting_param = JsonParameter('input_1', 'integer')
        with self.assertRaises(InvalidInterfaceConnection) as context:
            json_param.validate_connection(connecting_param)
        self.assertEqual(context.exception.error.name, 'MISMATCHED_JSON_TYPE')

        # Valid parameter connection
        connecting_param = JsonParameter('input_1', 'string')
        warnings = json_param.validate_connection(connecting_param)
        self.assertListEqual(warnings, [])
