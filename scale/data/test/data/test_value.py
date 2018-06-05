from __future__ import unicode_literals

import django

from django.test.testcases import TestCase

from data.data.exceptions import InvalidData
from data.data.value import FileValue, JsonValue
from data.interface.parameter import FileParameter, JsonParameter


class TestFileValue(TestCase):
    """Tests related to the FileValue class"""

    def setUp(self):
        django.setup()

    def test_validate(self):
        """Tests calling FileValue.validate()"""

        file_param = FileParameter('input_1', ['application/json'])
        json_param = JsonParameter('input_1', 'string')
        file_value = FileValue('input_1', [1234, 1235])

        # Invalid parameter type
        with self.assertRaises(InvalidData) as context:
            file_value.validate(json_param)
        self.assertEqual(context.exception.error.name, 'MISMATCHED_PARAM_TYPE')

        # Zero files not accepted
        file_value = FileValue('input_1', [])
        with self.assertRaises(InvalidData) as context:
            file_value.validate(file_param)
        self.assertEqual(context.exception.error.name, 'NO_FILES')

        # Multiple files not accepted
        file_value = FileValue('input_1', [1234, 1235])
        with self.assertRaises(InvalidData) as context:
            file_value.validate(file_param)
        self.assertEqual(context.exception.error.name, 'MULTIPLE_FILES')

        # Valid data value
        file_value = FileValue('input_1', [1234])
        warnings = file_value.validate(file_param)
        self.assertListEqual(warnings, [])


class TestJsonValue(TestCase):
    """Tests related to the JsonValue class"""

    def setUp(self):
        django.setup()

    def test_validate(self):
        """Tests calling JsonValue.validate()"""

        file_param = FileParameter('input_1', ['application/json'])
        json_param = JsonParameter('input_1', 'string')
        json_value = JsonValue('input_1', 'hello')

        # Invalid parameter type
        with self.assertRaises(InvalidData) as context:
            json_value.validate(file_param)
        self.assertEqual(context.exception.error.name, 'MISMATCHED_PARAM_TYPE')

        # Invalid array
        json_param = JsonParameter('input_1', 'array')
        json_value = JsonValue('input_1', 123)
        with self.assertRaises(InvalidData) as context:
            json_value.validate(json_param)
        self.assertEqual(context.exception.error.name, 'INVALID_JSON_TYPE')

        # Invalid boolean
        json_param = JsonParameter('input_1', 'boolean')
        json_value = JsonValue('input_1', 123)
        with self.assertRaises(InvalidData) as context:
            json_value.validate(json_param)
        self.assertEqual(context.exception.error.name, 'INVALID_JSON_TYPE')

        # Invalid integer
        json_param = JsonParameter('input_1', 'integer')
        json_value = JsonValue('input_1', 123.5)
        with self.assertRaises(InvalidData) as context:
            json_value.validate(json_param)
        self.assertEqual(context.exception.error.name, 'INVALID_JSON_TYPE')

        # Invalid number
        json_param = JsonParameter('input_1', 'number')
        json_value = JsonValue('input_1', 'foo')
        with self.assertRaises(InvalidData) as context:
            json_value.validate(json_param)
        self.assertEqual(context.exception.error.name, 'INVALID_JSON_TYPE')

        # Invalid object
        json_param = JsonParameter('input_1', 'object')
        json_value = JsonValue('input_1', 123)
        with self.assertRaises(InvalidData) as context:
            json_value.validate(json_param)
        self.assertEqual(context.exception.error.name, 'INVALID_JSON_TYPE')

        # Invalid string
        json_param = JsonParameter('input_1', 'string')
        json_value = JsonValue('input_1', 123)
        with self.assertRaises(InvalidData) as context:
            json_value.validate(json_param)
        self.assertEqual(context.exception.error.name, 'INVALID_JSON_TYPE')

        # Valid array value
        json_param = JsonParameter('input_1', 'array')
        json_value = JsonValue('input_1', [1, 2, 3])
        warnings = json_value.validate(json_param)
        self.assertListEqual(warnings, [])

        # Valid boolean value
        json_param = JsonParameter('input_1', 'boolean')
        json_value = JsonValue('input_1', True)
        warnings = json_value.validate(json_param)
        self.assertListEqual(warnings, [])

        # Valid integer value
        json_param = JsonParameter('input_1', 'integer')
        json_value = JsonValue('input_1', 1234)
        warnings = json_value.validate(json_param)
        self.assertListEqual(warnings, [])

        # Valid number value
        json_param = JsonParameter('input_1', 'number')
        json_value = JsonValue('input_1', 1234.5)
        warnings = json_value.validate(json_param)
        self.assertListEqual(warnings, [])

        # Valid object value
        json_param = JsonParameter('input_1', 'object')
        json_value = JsonValue('input_1', {'foo': 'bar'})
        warnings = json_value.validate(json_param)
        self.assertListEqual(warnings, [])

        # Valid string value
        json_param = JsonParameter('input_1', 'string')
        json_value = JsonValue('input_1', 'hello')
        warnings = json_value.validate(json_param)
        self.assertListEqual(warnings, [])
