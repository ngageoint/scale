'''Defines decorators for performing function retries with exponential backoff'''
import logging
import random
import time

from django.db.utils import OperationalError


logger = logging.getLogger(__name__)


def retry(no_arg_func=None, ex_class=Exception, max_tries=3, base_ms_delay=1000, max_ms_delay=30000):
    '''Wraps the decorated function so that it is retried with exponential backoff. On the first retry, the delay is a
    random number of milliseconds between 0 and base_ms_delay. The upper bound is then doubled for each successive
    retry. A retry delay will not exceed max_ms_delay milliseconds.

    :param no_arg_func: The function to retry (only populated if decorator used without args)
    :type no_arg_func: function
    :param ex_class: The exception(s) that should cause the function to retry
    :type ex_class: class or tuple of classes
    :param max_tries: The maximum number of times to call the function
    :type max_tries: int
    :param base_ms_delay: The base time to delay in milliseconds before retrying the function
    :type base_ms_delay: int
    :param max_ms_delay: The maximum time to delay in milliseconds
    :type max_ms_delay: int
    '''

    def func_decorator(func):

        def retry_wrapper(*args, **kwargs):

            tries = 0
            tries_remaining = max_tries - tries

            while tries_remaining > 1:

                try:
                    return func(*args, **kwargs)
                except ex_class as ex:
                    sleep_in_ms = random.randint(0, min(max_ms_delay, base_ms_delay * 2 ** tries))
                    sleep_in_secs = sleep_in_ms / 1000.0
                    msg = '%s threw %s, retrying after %s seconds'
                    logger.warning(msg, func.__name__, ex.__class__.__name__, str(sleep_in_secs))
                    time.sleep(sleep_in_secs)

                tries += 1
                tries_remaining = max_tries - tries

            # Execute final try
            if tries_remaining == 1:
                return func(*args, **kwargs)

        return retry_wrapper

    if callable(no_arg_func):
        # Function was passed in, so this is a decorator without args
        return func_decorator(no_arg_func)
    return func_decorator


def retry_database_query(no_arg_func=None, max_tries=5, base_ms_delay=1000, max_ms_delay=30000):
    '''Wraps the decorated function so that it is retried with exponential backoff if any operational database errors
    (disconnect, too many connections, etc) occurs. On the first retry, the delay is a random number of milliseconds
    between 0 and base_ms_delay. The upper bound is then doubled for each successive retry. A retry delay will not
    exceed max_ms_delay milliseconds.

    :param no_arg_func: The function to retry (only populated if decorator used without args)
    :type no_arg_func: function
    :param max_tries: The maximum number of times to call the function
    :type max_tries: int
    :param base_ms_delay: The base time to delay in milliseconds before retrying the function
    :type base_ms_delay: int
    :param max_ms_delay: The maximum time to delay in milliseconds
    :type max_ms_delay: int
    '''

    return retry(no_arg_func=no_arg_func, ex_class=OperationalError, max_tries=max_tries, base_ms_delay=base_ms_delay,
                 max_ms_delay=max_ms_delay)
