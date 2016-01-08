'''Defines the abstract base class used for cleaning up job executions'''
from __future__ import unicode_literals

import logging
import os

from ingest.file_system import get_ingest_work_dir
from job.execution.job_exe_cleaner import JobExecutionCleaner
from storage.nfs import nfs_umount


logger = logging.getLogger(__name__)


class IngestJobExecutionCleaner(JobExecutionCleaner):
    '''Cleaner for the execution of ingest jobs
    '''

    def cleanup_job_execution(self, job_exe):
        '''See :meth:`job.execution.job_exe_cleaner.JobExecutionCleaner.cleanup_job_execution`
        '''

        logger.info('Cleaning up an ingest job')

        ingest_work_dir = get_ingest_work_dir(job_exe.id)

        if os.path.exists(ingest_work_dir):
            nfs_umount(ingest_work_dir)
            logger.info('Deleting %s', ingest_work_dir)
            os.rmdir(ingest_work_dir)
