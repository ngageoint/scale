'''Defines utility methods for testing ingests'''
import django.utils.timezone as timezone

import job.test.utils as job_utils
import source.test.utils as source_test_utils
import storage.test.utils as storage_test_utils
from ingest.models import Ingest, Strike

NAME_COUNTER = 1


def create_ingest(file_name='test.txt', status='TRANSFERRING', transfer_started=None, transfer_ended=None,
                  ingest_started=None, ingest_ended=None, data_started=None, data_ended=None, workspace=None,
                  strike=None, source_file=None):
    if not workspace:
        workspace = storage_test_utils.create_workspace()
    if not strike:
        strike = create_strike()
    if not source_file:
        source_file = source_test_utils.create_source(file_name=file_name, data_started=data_started,
                                                      data_ended=data_ended, workspace=workspace)
    if not transfer_started:
        transfer_started = timezone.now()
    if status not in ['QUEUED', 'TRANSFERRING'] and not ingest_started:
        ingest_started = timezone.now()
    if status not in ['QUEUED', 'TRANSFERRING', 'INGESTING'] and not ingest_ended:
        ingest_ended = timezone.now()

    try:
        job_type = Ingest.objects.get_ingest_job_type()
    except:
        job_type = job_utils.create_job_type()
    job = job_utils.create_job(job_type=job_type)
    job_utils.create_job_exe(job=job)

    return Ingest.objects.create(file_name=file_name, file_size=source_file.file_size, status=status,
                                 transfer_path='/test/transfer', job=job, bytes_transferred=source_file.file_size,
                                 transfer_started=transfer_started, transfer_ended=transfer_ended,
                                 media_type='text/plain', ingest_path='/test/ingest',
                                 ingest_started=ingest_started, ingest_ended=ingest_ended,
                                 workspace=workspace, strike=strike, source_file=source_file)


def create_strike(name=None, title=None, description=None, configuration=None, job=None):
    if not name:
        global NAME_COUNTER
        name = u'test-strike-%i' % NAME_COUNTER
        NAME_COUNTER = NAME_COUNTER + 1
    if not title:
        title = 'Test Strike'
    if not description:
        description = 'Test description'
    if not configuration:
        configuration = {'version': '1.0'}
    if not job:
        job = job_utils.create_job()

    return Strike.objects.create(name=name, title=title, description=description, configuration=configuration, job=job)
