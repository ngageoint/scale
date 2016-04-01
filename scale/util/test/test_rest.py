#@PydevCodeAnalysisIgnore
import datetime

import django
import django.utils.timezone as timezone
import mock
from django.http import QueryDict
from django.test import TestCase
from mock import MagicMock
from rest_framework.request import Request

import util.rest as rest_util
from util.rest import BadParameter, ReadOnly


class TestRest(TestCase):

    def setUp(self):
        django.setup()

    def test_check_update(self):
        '''Tests checking a white-list of parameters allowed to be updated during a POST.'''
        request = MagicMock(Request)
        request.data = QueryDict('', mutable=True)
        request.data.update({
            'test': 'value1',
        })
        self.assertTrue(rest_util.check_update(request, ['test']))

    def test_check_bad_param_type(self):
        '''Tests checking a white-list of invalid parameters allowed to be updated during a POST.'''
        request = MagicMock(Request)
        request.data = QueryDict('', mutable=True)
        request.data.update({
            'test1': 'value1',
            'test2': 'value2',
        })
        self.assertRaises(AssertionError, rest_util.check_update, request, 'test1')

    def test_check_update_invalid(self):
        '''Tests checking a white-list of invalid parameters allowed to be updated during a POST.'''
        request = MagicMock(Request)
        request.data = QueryDict('', mutable=True)
        request.data.update({
            'test1': 'value1',
            'test2': 'value2',
        })
        self.assertRaises(ReadOnly, rest_util.check_update, request, ['test1'])

    def test_check_time_range(self):
        '''Tests checking a time range is valid.'''
        self.assertTrue(rest_util.check_time_range(datetime.datetime(2015, 1, 1), datetime.datetime(2015, 1, 30)))

    def test_check_time_range_partial(self):
        '''Tests checking a partial time range is valid.'''
        self.assertTrue(rest_util.check_time_range(datetime.datetime(2015, 1, 1), None))
        self.assertTrue(rest_util.check_time_range(None, datetime.datetime(2015, 1, 30)))

    def test_check_time_range_equal(self):
        '''Tests checking a time range that is invalid due to being equal.'''
        self.assertRaises(BadParameter, rest_util.check_time_range, datetime.datetime(2015, 1, 1),
                          datetime.datetime(2015, 1, 1))

    def test_check_time_range_flipped(self):
        '''Tests checking a time range that is invalid due to start being after end.'''
        self.assertRaises(BadParameter, rest_util.check_time_range, datetime.datetime(2015, 1, 30),
                          datetime.datetime(2015, 1, 1))

    def test_check_time_range_duration(self):
        '''Tests checking a time range that is invalid due to max duration exceeded.'''
        self.assertRaises(BadParameter, rest_util.check_time_range, datetime.datetime(2015, 1, 1),
                          datetime.datetime(2015, 3, 1), datetime.timedelta(days=31))

    def test_check_together_empty(self):
        '''Tests checking multiple parameters together when none are given.'''
        self.assertFalse(rest_util.check_together([], []))

    def test_check_together_none(self):
        '''Tests checking multiple parameters together when none are given.'''
        self.assertFalse(rest_util.check_together(['test1', 'test2'], [None, None]))

    def test_check_together_single(self):
        '''Tests checking multiple parameters together when one is given.'''
        self.assertFalse(rest_util.check_together(['test1'], [None]))

    def test_check_together_partial(self):
        '''Tests checking multiple parameters together when some are given.'''
        self.assertRaises(BadParameter, rest_util.check_together, ['test1', 'test2'], ['value1', None])

    def test_check_together_all(self):
        '''Tests checking multiple parameters together.'''
        self.assertTrue(rest_util.check_together(['test1', 'test2'], ['value1', 'value2']))

    def test_has_params_empty(self):
        '''Tests checking parameter presence when none are given.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        self.assertFalse(rest_util.has_params(request))

    def test_has_params_none(self):
        '''Tests checking parameter presence when none are given.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        self.assertFalse(rest_util.has_params(request, None, None))

    def test_has_params_single(self):
        '''Tests checking parameter presence when one is given.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test1': 'value1',
        })
        self.assertTrue(rest_util.has_params(request, 'test1'))

    def test_has_params_partial(self):
        '''Tests checking parameter presence when some are given.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test1': 'value1',
        })
        self.assertFalse(rest_util.has_params(request, 'test1', 'test2'))

    def test_has_params_all(self):
        '''Tests checking parameter presence when all are given.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test1': 'value1',
            'test2': None,
        })
        self.assertTrue(rest_util.has_params(request, 'test1', 'test2'))

    def test_parse_string(self):
        '''Tests parsing a required string parameter that is provided via GET.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': 'value1',
        })
        self.assertEqual(rest_util.parse_string(request, 'test'), 'value1')

    def test_parse_string_missing(self):
        '''Tests parsing a required string parameter that is missing.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': 'value1',
        })
        self.assertRaises(BadParameter, rest_util.parse_string, request, 'test2')

    def test_parse_string_default(self):
        '''Tests parsing an optional string parameter that is provided via default value.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': 'value1',
        })
        self.assertEqual(rest_util.parse_string(request, 'test2', 'value2'), 'value2')

    def test_parse_string_optional(self):
        '''Tests parsing an optional string parameter that is missing.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': 'value1',
        })
        self.assertIsNone(rest_util.parse_string(request, 'test2', required=False))

    def test_parse_string_accepted_none(self):
        '''Tests parsing a string parameter where the value is not acceptable.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': 'value1',
        })

        self.assertRaises(BadParameter, rest_util.parse_string, request, 'test', accepted_values=['value'])

    def test_parse_string_accepted_all(self):
        '''Tests parsing a string parameter where the value is acceptable.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': 'value1',
        })

        self.assertEqual(rest_util.parse_string(request, 'test', accepted_values=['value1']), 'value1')

    def test_parse_string_post(self):
        '''Tests parsing a required string parameter that is provided via POST.'''
        request = MagicMock(Request)
        request.data = QueryDict('', mutable=True)
        request.data.update({
            'test': 'value1',
        })
        self.assertEqual(rest_util.parse_string(request, 'test'), 'value1')

    def test_parse_string_list(self):
        '''Tests parsing a required list of string parameters that is provided via GET.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.setlist('test', ['value1', 'value2'])

        self.assertListEqual(rest_util.parse_string_list(request, 'test'), ['value1', 'value2'])

    def test_parse_string_list_missing(self):
        '''Tests parsing a required list of string parameters that are missing.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.setlist('test', ['value1', 'value2'])

        self.assertRaises(BadParameter, rest_util.parse_string_list, request, 'test2')

    def test_parse_string_list_default(self):
        '''Tests parsing a required list of string parameters that are provided via default value.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.setlist('test', ['value1'])

        self.assertEqual(rest_util.parse_string_list(request, 'test2', ['value2', 'value3']), ['value2', 'value3'])

    def test_parse_string_list_optional(self):
        '''Tests parsing an optional list of string parameters that are missing.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.setlist('test', ['value1'])

        self.assertListEqual(rest_util.parse_string_list(request, 'test2', required=False), [])

    def test_parse_string_list_accepted_none(self):
        '''Tests parsing a list of string parameters where none of the values are acceptable.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.setlist('test', ['value1', 'value2'])

        self.assertRaises(BadParameter, rest_util.parse_string_list, request, 'test', accepted_values=['value'])

    def test_parse_string_list_accepted_partial(self):
        '''Tests parsing a list of string parameters where only some values are acceptable.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.setlist('test', ['value1', 'value2'])

        self.assertRaises(BadParameter, rest_util.parse_string_list, request, 'test', accepted_values=['value1'])

    def test_parse_string_list_accepted_all(self):
        '''Tests parsing a list of string parameters where all values are acceptable.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.setlist('test', ['value1', 'value2'])

        self.assertListEqual(rest_util.parse_string_list(request, 'test', accepted_values=['value1', 'value2']),
                             ['value1', 'value2'])

    def test_parse_string_list_post(self):
        '''Tests parsing a required list of string parameters that are provided via POST.'''
        request = MagicMock(Request)
        request.data = QueryDict('', mutable=True)
        request.data.update({
            'test': ['value1', 'value2']
        })

        self.assertEqual(rest_util.parse_string_list(request, 'test'), ['value1', 'value2'])

    def test_parse_bool_true(self):
        '''Tests parsing a required bool parameter that is provided via GET.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test1': 'TRUE',
            'test2': 'True',
            'test3': 'true',
            'test4': 't',
            'test5': '1',
        })

        self.assertTrue(rest_util.parse_bool(request, 'test1'))
        self.assertTrue(rest_util.parse_bool(request, 'test2'))
        self.assertTrue(rest_util.parse_bool(request, 'test3'))
        self.assertTrue(rest_util.parse_bool(request, 'test4'))
        self.assertTrue(rest_util.parse_bool(request, 'test5'))

    def test_parse_bool_false(self):
        '''Tests parsing a required bool parameter that is provided via GET.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test1': 'FALSE',
            'test2': 'False',
            'test3': 'false',
            'test4': 'f',
            'test5': '0',
        })

        self.assertFalse(rest_util.parse_bool(request, 'test1'))
        self.assertFalse(rest_util.parse_bool(request, 'test2'))
        self.assertFalse(rest_util.parse_bool(request, 'test3'))
        self.assertFalse(rest_util.parse_bool(request, 'test4'))
        self.assertFalse(rest_util.parse_bool(request, 'test5'))

    def test_parse_bool_missing(self):
        '''Tests parsing a required bool parameter that is missing.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': 'true',
        })
        self.assertRaises(BadParameter, rest_util.parse_bool, request, 'test2')

    def test_parse_bool_default(self):
        '''Tests parsing an optional bool parameter that is provided via default value.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': 'true',
        })
        self.assertFalse(rest_util.parse_bool(request, 'test2', False))

    def test_parse_bool_optional(self):
        '''Tests parsing an optional bool parameter that is missing.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': 'true',
        })
        self.assertIsNone(rest_util.parse_bool(request, 'test2', required=False))

    def test_parse_bool_post(self):
        '''Tests parsing a required bool parameter that is provided via POST.'''
        request = MagicMock(Request)
        request.data = QueryDict('', mutable=True)
        request.data.update({
            'test': 'true',
        })
        self.assertTrue(rest_util.parse_bool(request, 'test'))

    def test_parse_int(self):
        '''Tests parsing a required int parameter that is provided via GET.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': '10',
        })
        self.assertEqual(rest_util.parse_int(request, 'test'), 10)

    def test_parse_int_missing(self):
        '''Tests parsing a required int parameter that is missing.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': '10',
        })
        self.assertRaises(BadParameter, rest_util.parse_int, request, 'test2')

    def test_parse_int_default(self):
        '''Tests parsing a required int parameter that is provided via default value.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': '10',
        })
        self.assertEqual(rest_util.parse_int(request, 'test2', 20), 20)

    def test_parse_int_optional(self):
        '''Tests parsing an optional int parameter that is missing.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': 'value1',
        })
        self.assertIsNone(rest_util.parse_int(request, 'test2', required=False))

    def test_parse_int_accepted_none(self):
        '''Tests parsing an int parameter where the value is not acceptable.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': '1',
        })

        self.assertRaises(BadParameter, rest_util.parse_int, request, 'test', accepted_values=[5, 10])

    def test_parse_int_accepted_all(self):
        '''Tests parsing an int parameter where the value is acceptable.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': '1',
        })

        self.assertEqual(rest_util.parse_int(request, 'test', accepted_values=[1, 2, 3]), 1)

    def test_parse_int_zero(self):
        '''Tests parsing an optional int parameter zero instead of using the default value.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': '0',
        })
        self.assertEqual(rest_util.parse_int(request, 'test', 10), 0)

    def test_parse_int_invalid(self):
        '''Tests parsing a required int parameter that is not a valid number.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': 'abc',
        })
        self.assertRaises(BadParameter, rest_util.parse_int, request, 'test')

    def test_parse_int_post(self):
        '''Tests parsing a required int parameter that is provided via POST.'''
        request = MagicMock(Request)
        request.data = QueryDict('', mutable=True)
        request.data.update({
            'test': '10',
        })
        self.assertEqual(rest_util.parse_int(request, 'test'), 10)

    def test_parse_int_list(self):
        '''Tests parsing a required list of int parameters that is provided via GET.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.setlist('test', ['1', '2'])

        self.assertListEqual(rest_util.parse_int_list(request, 'test'), [1, 2])

    def test_parse_int_list_missing(self):
        '''Tests parsing a required list of int parameters that are missing.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.setlist('test', ['1', '2'])
        self.assertRaises(BadParameter, rest_util.parse_int_list, request, 'test2')

    def test_parse_int_list_default(self):
        '''Tests parsing a required list of int parameters that are provided via default value.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.setlist('test', ['1'])
        self.assertEqual(rest_util.parse_int_list(request, 'test2', ['2', '3']), [2, 3])

    def test_parse_int_list_optional(self):
        '''Tests parsing an optional list of int parameters that are missing.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.setlist('test', ['1'])
        self.assertListEqual(rest_util.parse_int_list(request, 'test2', required=False), [])

    def test_parse_int_list_accepted_none(self):
        '''Tests parsing a list of int parameters where none of the values are acceptable.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.setlist('test', ['1', '2'])

        self.assertRaises(BadParameter, rest_util.parse_int_list, request, 'test', accepted_values=[3])

    def test_parse_int_list_accepted_partial(self):
        '''Tests parsing a list of int parameters where only some values are acceptable.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.setlist('test', ['1', '2'])

        self.assertRaises(BadParameter, rest_util.parse_int_list, request, 'test', accepted_values=[1])

    def test_parse_int_list_accepted_all(self):
        '''Tests parsing a list of int parameters where all values are acceptable.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.setlist('test', ['1', '2'])

        self.assertListEqual(rest_util.parse_int_list(request, 'test', accepted_values=[1, 2]), [1, 2])

    def test_parse_int_list_post(self):
        '''Tests parsing a required list of int parameters that are provided via POST.'''
        request = MagicMock(Request)
        request.data = QueryDict('', mutable=True)
        request.data.update({
            'test': ['1', '2']
        })

        self.assertEqual(rest_util.parse_int_list(request, 'test'), [1, 2])

    def test_parse_float(self):
        '''Tests parsing a required float parameter that is provided via GET.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': '10.1',
        })
        self.assertEqual(rest_util.parse_float(request, 'test'), 10.1)

    def test_parse_float_missing(self):
        '''Tests parsing a required float parameter that is missing.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': '10.1',
        })
        self.assertRaises(BadParameter, rest_util.parse_float, request, 'test2')

    def test_parse_float_default(self):
        '''Tests parsing a required float parameter that is provided via default value.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': '10.1',
        })
        self.assertEqual(rest_util.parse_float(request, 'test2', 20.1), 20.1)

    def test_parse_float_optional(self):
        '''Tests parsing an optional float parameter that is missing.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': 'value1',
        })
        self.assertIsNone(rest_util.parse_float(request, 'test2', required=False))

    def test_parse_float_accepted_none(self):
        '''Tests parsing a float parameter where the value is not acceptable.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': '1.0',
        })

        self.assertRaises(BadParameter, rest_util.parse_float, request, 'test', accepted_values=[5.0, 10.0])

    def test_parse_float_valid(self):
        '''Tests parsing a float parameter where the value is acceptable.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': '1.1',
        })

        self.assertEqual(rest_util.parse_float(request, 'test', accepted_values=[1.1, 2.2, 3.3]), 1.1)

    def test_parse_float_zero(self):
        '''Tests parsing an optional float parameter zero instead of using the default value.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': '0.0',
        })
        self.assertEqual(rest_util.parse_float(request, 'test', 10.1), 0.0)

    def test_parse_float_invalid(self):
        '''Tests parsing a required float parameter that is not a valid number.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': 'abc',
        })
        self.assertRaises(BadParameter, rest_util.parse_float, request, 'test')

    def test_parse_float_post(self):
        '''Tests parsing a required float parameter that is provided via POST.'''
        request = MagicMock(Request)
        request.data = QueryDict('', mutable=True)
        request.data.update({
            'test': '10.1',
        })
        self.assertEqual(rest_util.parse_float(request, 'test'), 10.1)

    def test_parse_duration(self):
        '''Tests parsing a required ISO duration parameter that is provided via GET.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': 'PT3H0M0S',
        })
        self.assertEqual(rest_util.parse_duration(request, 'test'), datetime.timedelta(0, 10800))

    def test_parse_duration_missing(self):
        '''Tests parsing a required ISO duration parameter that is missing.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': '10',
        })
        self.assertRaises(BadParameter, rest_util.parse_duration, request, 'test2')

    def test_parse_duration_default(self):
        '''Tests parsing a required ISO duration parameter that is provided via default value.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': 'PT3H0M0S',
        })
        default_value = datetime.timedelta(0, 20800)
        self.assertEqual(rest_util.parse_duration(request, 'test2', default_value), default_value)

    def test_parse_duration_optional(self):
        '''Tests parsing an optional ISO duration parameter that is missing.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': 'value1',
        })
        self.assertIsNone(rest_util.parse_duration(request, 'test2', required=False))

    def test_parse_duration_invalid(self):
        '''Tests parsing a required ISO duration parameter that is formatted incorrectly.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': 'BAD',
        })
        self.assertRaises(BadParameter, rest_util.parse_duration, request, 'test')

    def test_parse_datetime(self):
        '''Tests parsing a valid ISO datetime.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': '2015-01-01T00:00:00Z',
        })
        self.assertEqual(rest_util.parse_datetime(request, 'test'), datetime.datetime(2015, 1, 1, tzinfo=timezone.utc))

    def test_parse_datetime_missing(self):
        '''Tests parsing a required ISO datetime parameter that is missing.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': '10',
        })
        self.assertRaises(BadParameter, rest_util.parse_datetime, request, 'test2')

    def test_parse_datetime_default(self):
        '''Tests parsing a required ISO datetime parameter that is provided via default value.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': '2015-01-01T00:00:00Z',
        })
        default_value = datetime.datetime(2015, 2, 10, tzinfo=timezone.utc)
        self.assertEqual(rest_util.parse_datetime(request, 'test2', default_value), default_value)

    def test_parse_datetime_optional(self):
        '''Tests parsing an optional ISO datetime parameter that is missing.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': 'value1',
        })
        self.assertIsNone(rest_util.parse_datetime(request, 'test2', required=False))

    def test_parse_datetime_invalid(self):
        '''Tests parsing a required ISO datetime parameter that is formatted incorrectly.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': '20150101T00:00:00Z',
        })
        self.assertRaises(BadParameter, rest_util.parse_datetime, request, 'test')

    def test_parse_datetime_missing_timezone(self):
        '''Tests parsing an ISO datetime missing a timezone.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': '2015-01-01T00:00:00',
        })
        self.assertRaises(BadParameter, rest_util.parse_datetime, request, 'test')

    @mock.patch('django.utils.timezone.now')
    def test_parse_timestamp_duration(self, mock_now):
        '''Tests parsing a valid ISO duration.'''
        mock_now.return_value = datetime.datetime(2015, 1, 1, 10, tzinfo=timezone.utc)
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': 'PT3H0M0S',
        })
        self.assertEqual(rest_util.parse_timestamp(request, 'test'),
                         datetime.datetime(2015, 1, 1, 7, tzinfo=timezone.utc))

    def test_parse_timestamp_datetime(self):
        '''Tests parsing a valid ISO datetime.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': '2015-01-01T00:00:00Z',
        })
        self.assertEqual(rest_util.parse_timestamp(request, 'test'), datetime.datetime(2015, 1, 1, tzinfo=timezone.utc))

    def test_parse_dict(self):
        '''Tests parsing a dictionary.'''
        result = {
            'name': 'value',
        }
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        request.query_params.update({
            'test': result,
        })
        self.assertDictEqual(rest_util.parse_dict(request, 'test'), result)

    def test_parse_dict_optional(self):
        '''Tests parsing an optional dict with no default value.'''
        request = MagicMock(Request)
        request.query_params = QueryDict('', mutable=True)
        self.assertDictEqual(rest_util.parse_dict(request, 'test', required=False), {})
