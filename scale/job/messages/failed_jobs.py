"""Defines a command message that sets FAILED status for job models"""
from __future__ import unicode_literals

import logging
from collections import namedtuple

from django.db import transaction

from error.models import get_error
from job.models import Job
from messaging.messages.message import CommandMessage
from util.parse import datetime_to_string, parse_datetime

# This is the maximum number of job models that can fit in one message. This maximum ensures that every message of this
# type is less than 25 KiB long.
MAX_NUM = 100


FailedJob = namedtuple('FailedJob', ['job_id', 'exe_num'])


logger = logging.getLogger(__name__)


class FailedJobs(CommandMessage):
    """Command message that sets FAILED status for job models
    """

    def __init__(self):
        """Constructor
        """

        super(FailedJobs, self).__init__('failed_jobs')

        self._count = 0
        self._failed_jobs = {}  # {Error ID: [FailedJob]}
        self.ended = None

    def add_failed_job(self, job_id, exe_num, error_id):
        """Adds the given failed job to this message

        :param job_id: The failed job ID
        :type job_id: int
        :param exe_num: The failed job's execution number
        :type exe_num: int
        :param error_id: The error ID for the failure
        :type error_id: int
        """

        self._count += 1
        failed_job = FailedJob(job_id, exe_num)
        if error_id in self._failed_jobs:
            self._failed_jobs[error_id].append(failed_job)
        else:
            self._failed_jobs[error_id] = [failed_job]

    def can_fit_more(self):
        """Indicates whether more failed jobs can fit in this message

        :return: True if more failed jobs can fit, False otherwise
        :rtype: bool
        """

        return self._count < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        error_list = []
        for error_id, job_list in self._failed_jobs.items():
            jobs_list = []
            for failed_job in job_list:
                jobs_list.append({'id': failed_job.job_id, 'exe_num': failed_job.exe_num})
            error_list.append({'id': error_id, 'jobs': jobs_list})

        return {'ended': datetime_to_string(self.ended), 'errors': error_list}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = FailedJobs()
        message.ended = parse_datetime(json_dict['ended'])

        for error_dict in json_dict['errors']:
            error_id = error_dict['id']
            for job_dict in error_dict['jobs']:
                job_id = job_dict['id']
                exe_num = job_dict['exe_num']
                message.add_failed_job(job_id, exe_num, error_id)

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        job_ids = []
        for job_list in self._failed_jobs.values():
            for failed_job in job_list:
                job_ids.append(failed_job.job_id)

        with transaction.atomic():
            # Retrieve locked job models
            job_models = {}
            for job in Job.objects.get_locked_jobs(job_ids):
                job_models[job.id] = job

            # TODO: implement
            job_ids_for_status_update = []
            for error_id, job_list in self._failed_jobs.items():
                error = get_error(error_id)
                job_ids_for_node_update = []
                for job_tuple in job_list:
                    job_id = job_tuple[0]
                    exe_num = job_tuple[1]
                    job_model = job_models[job_id]
                    if job_model.num_exes != exe_num:
                        continue  # Execution number does not match so this update is out of date, ignore job
                    # Execution numbers match, so this job needs to have its node_id set
                    job_ids_for_node_update.append(job_id)
                    # Check status because if it is not QUEUED, then this update came too late (after job already
                    # reached a final status) and we don't want to update status then
                    if job_model.status == 'QUEUED':
                        # Job status is still QUEUED, so update to RUNNING
                        job_ids_for_status_update.append(job_id)

                # Update jobs for this node
                if job_ids_for_node_update:
                    Job.objects.update_jobs_node(job_ids_for_node_update, node_id, self._started)

            # Update jobs that need status set to RUNNING
            if job_ids_for_status_update:
                logger.info('Setting %d job(s) to RUNNING status', len(job_ids_for_status_update))
                Job.objects.update_jobs_to_running(job_ids_for_status_update, self._started)

        return True
