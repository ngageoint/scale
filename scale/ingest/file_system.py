'''Defines methods for necessary file system interactions to perform file ingests'''
from __future__ import unicode_literals

import os

from job.execution.file_system import get_job_exe_dir


def get_ingest_work_dir(job_exe_id):
    '''Returns the work directory that a job execution can use to perform an ingest

    :param job_exe_id: The ID of the job execution
    :type job_exe_id: int
    :returns: The absolute path of the ingest work directory
    :rtype: str
    '''

    job_exe_dir = get_job_exe_dir(job_exe_id)
    return os.path.join(job_exe_dir, 'ingest_work')
