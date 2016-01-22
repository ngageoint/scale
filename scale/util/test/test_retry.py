#@PydevCodeAnalysisIgnore
import datetime

import django
from django.test import SimpleTestCase
from mock import MagicMock, call, patch

from util.retry import retry


class TestRetry(SimpleTestCase):
    '''Tests the retry decorator function'''

    def setUp(self):
        django.setup()

    @retry
    def always_fail_no_decorator_args(self):
        raise Exception('Bad!')

    @retry(ex_class=Exception, max_tries=3, base_ms_delay=1000, max_ms_delay=30000)
    def always_fail(self):
        raise Exception('Bad!')

    @retry(ex_class=Exception, max_tries=10, base_ms_delay=2000, max_ms_delay=30000)
    def always_fail_10_times(self):
        raise Exception('Bad!')

    @retry(ex_class=IOError)
    def wrong_exception(self):
        raise ArithmeticError('Bad!')

    @patch('util.retry.time.sleep')
    @patch('util.retry.random.randint')
    def test_always_fail_no_decorator_args(self, mock_randint, mock_sleep):
        '''Tests retrying always_fail_no_decorator_args()'''
        mock_randint.return_value = 1

        self.assertRaises(Exception, self.always_fail)

        mock_randint.assert_has_calls([call(0, 1000), call(0, 2000)])
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('util.retry.time.sleep')
    @patch('util.retry.random.randint')
    def test_always_fail(self, mock_randint, mock_sleep):
        '''Tests retrying always_fail()'''
        mock_randint.return_value = 1

        self.assertRaises(Exception, self.always_fail)

        mock_randint.assert_has_calls([call(0, 1000), call(0, 2000)])
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('util.retry.time.sleep')
    @patch('util.retry.random.randint')
    def test_always_fail_10_times(self, mock_randint, mock_sleep):
        '''Tests retrying always_fail_10_times()'''
        mock_randint.return_value = 1

        self.assertRaises(Exception, self.always_fail_10_times)

        mock_randint.assert_has_calls([call(0, 2000), call(0, 4000), call(0, 8000), call(0, 16000), call(0, 30000), call(0, 30000), call(0, 30000), call(0, 30000), call(0, 30000)])
        self.assertEqual(mock_sleep.call_count, 9)

    @patch('util.retry.time.sleep')
    @patch('util.retry.random.randint')
    def test_wrong_exception(self, mock_randint, mock_sleep):
        '''Tests retrying wrong_exception()'''
        mock_randint.return_value = 1

        self.assertRaises(ArithmeticError, self.wrong_exception)

        self.assertEqual(mock_randint.call_count, 0)
        self.assertEqual(mock_sleep.call_count, 0)
