import datetime

from django.db.utils import OperationalError
from django.test import SimpleTestCase
from mock import MagicMock, call, patch

from util.retry import retry, retry_database_query


class TestRetry(SimpleTestCase):
    '''Tests the retry decorator function'''

    @retry
    def success(self):
        pass

    @retry
    def success_with_return(self):
        return 1

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
    def test_success(self, mock_randint, mock_sleep):
        '''Tests retrying success()'''
        mock_randint.return_value = 1

        self.success()

        self.assertEqual(mock_randint.call_count, 0)
        self.assertEqual(mock_sleep.call_count, 0)

    @patch('util.retry.time.sleep')
    @patch('util.retry.random.randint')
    def test_success_with_return(self, mock_randint, mock_sleep):
        '''Tests retrying success_with_return()'''
        mock_randint.return_value = 1

        result = self.success_with_return()

        self.assertEqual(result, 1)
        self.assertEqual(mock_randint.call_count, 0)
        self.assertEqual(mock_sleep.call_count, 0)

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


class TestRetryDatabaseQuery(SimpleTestCase):
    '''Tests the retry_database_query decorator function'''

    @retry_database_query
    def success_with_return(self):
        return 2

    @retry_database_query(max_tries=5, base_ms_delay=1000, max_ms_delay=30000)
    def always_fail(self):
        raise OperationalError

    @patch('util.retry.time.sleep')
    @patch('util.retry.random.randint')
    def test_success_with_return(self, mock_randint, mock_sleep):
        '''Tests retrying success_with_return()'''
        mock_randint.return_value = 1

        result = self.success_with_return()

        self.assertEqual(result, 2)
        self.assertEqual(mock_randint.call_count, 0)
        self.assertEqual(mock_sleep.call_count, 0)

    @patch('util.retry.time.sleep')
    @patch('util.retry.random.randint')
    def test_always_fail(self, mock_randint, mock_sleep):
        '''Tests retrying always_fail'''
        mock_randint.return_value = 1

        self.assertRaises(OperationalError, self.always_fail)

        mock_randint.assert_has_calls([call(0, 1000), call(0, 2000), call(0, 4000), call(0, 8000)])
        self.assertEqual(mock_sleep.call_count, 4)
