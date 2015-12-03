'''Defines utility methods for testing metrics'''
import django.utils.timezone as timezone

import ingest.test.utils as ingest_test_utils
import job.test.utils as job_test_utils
from metrics.models import MetricsIngest, MetricsJobType


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
