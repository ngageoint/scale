'''Defines utility methods for testing metrics'''
import django.utils.timezone as timezone

import error.test.utils as error_test_utils
import ingest.test.utils as ingest_test_utils
import job.test.utils as job_test_utils
from metrics.models import MetricsError, MetricsIngest, MetricsJobType


def create_error(error=None, occurred=None, **kwargs):
    '''Creates a metrics ingest model for unit testing

    :returns: The metrics ingest model
    :rtype: :class:`metrics.models.MetricsIngest`
    '''
    if not error:
        error = error_test_utils.create_error(is_builtin=True)
    if not occurred:
        occurred = timezone.now()

    return MetricsError.objects.create(error=error, occurred=occurred, **kwargs)


def create_ingest(strike=None, occurred=None, **kwargs):
    '''Creates a metrics ingest model for unit testing

    :returns: The metrics ingest model
    :rtype: :class:`metrics.models.MetricsIngest`
    '''
    if not strike:
        strike = ingest_test_utils.create_strike()
    if not occurred:
        occurred = timezone.now()

    return MetricsIngest.objects.create(strike=strike, occurred=occurred, **kwargs)


def create_job_type(job_type=None, occurred=None, **kwargs):
    '''Creates a metrics job type model for unit testing

    :returns: The metrics job type model
    :rtype: :class:`metrics.models.MetricsJobType`
    '''
    if not job_type:
        job_type = job_test_utils.create_job_type()
    if not occurred:
        occurred = timezone.now()

    return MetricsJobType.objects.create(job_type=job_type, occurred=occurred, **kwargs)
