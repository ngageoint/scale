"""Defines a command message that creates job_exe_end models"""
from __future__ import unicode_literals

import logging

from job.models import JobExecutionEnd
from messaging.messages.message import CommandMessage
from util.parse import datetime_to_string, parse_datetime

# This is the maximum number of job_exe_end models that can fit in one message. This maximum ensures that every message
# of this type is less than 25 KiB long.
MAX_NUM = 10


logger = logging.getLogger(__name__)


class CreateJobExecutionEnd(CommandMessage):
    """Command message that creates job_exe_end models
    """

    def __init__(self):
        """Constructor
        """

        super(CreateJobExecutionEnd, self).__init__('create_job_exe_end')

        self._job_exe_ends = []

    def add_job_exe_end(self, job_exe_end):
        """Adds the given job_exe_end model to this message

        :param job_exe_end: The job_exe_end model to add
        :type job_exe_end: :class:`job.models.JobExecutionEnd`
        """

        self._job_exe_ends.append(job_exe_end)

    def can_fit_more(self):
        """Indicates whether more job_exe_end models can fit in this message

        :return: True if more job_exe_end models can fit, False otherwise
        :rtype: bool
        """

        return len(self._job_exe_ends) < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        job_exe_end_list = []

        for job_exe_end in self._job_exe_ends:
            job_exe_end_dict = {'id': job_exe_end.job_exe_id, 'job_id': job_exe_end.job_id,
                                'job_type_id': job_exe_end.job_type_id, 'exe_num': job_exe_end.exe_num,
                                'tasks_results': job_exe_end.tasks_results, 'status': job_exe_end.status,
                                'queued': datetime_to_string(job_exe_end.queued),
                                'ended': datetime_to_string(job_exe_end.ended)}
            if job_exe_end.error_id:
                job_exe_end_dict['error_id'] = job_exe_end.error_id
            if job_exe_end.node_id:
                job_exe_end_dict['node_id'] = job_exe_end.node_id
            if job_exe_end.started:
                job_exe_end_dict['started'] = datetime_to_string(job_exe_end.started)
            job_exe_end_list.append(job_exe_end_dict)

        return {'job_exe_end_models': job_exe_end_list}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = CreateJobExecutionEnd()

        for job_exe_end_dict in json_dict['job_exe_end_models']:
            job_exe_end = JobExecutionEnd()
            job_exe_end.job_exe_id = job_exe_end_dict['id']
            job_exe_end.job_id = job_exe_end_dict['job_id']
            job_exe_end.job_type_id = job_exe_end_dict['job_type_id']
            job_exe_end.exe_num = job_exe_end_dict['exe_num']
            job_exe_end.task_results = job_exe_end_dict['task_results']
            job_exe_end.status = job_exe_end_dict['status']
            job_exe_end.queued = parse_datetime(job_exe_end_dict['queued'])
            job_exe_end.ended = parse_datetime(job_exe_end_dict['ended'])
            if 'error_id' in job_exe_end_dict:
                job_exe_end.error_id = job_exe_end_dict['error_id']
            if 'node_id' in job_exe_end_dict:
                job_exe_end.node_id = job_exe_end_dict['node_id']
            if 'started' in job_exe_end_dict:
                job_exe_end.started = job_exe_end_dict['started']
            message.add_job_exe_end(job_exe_end)

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        # See if any of the job_exe_end models already exist
        job_exe_ids = [job_exe_end.job_exe_id for job_exe_end in self._job_exe_ends]
        existing_ids = set(model.job_exe_id for model in JobExecutionEnd.objects.filter(job_exe_id__in=job_exe_ids))

        # Filter out job_exe_end models that already exist
        models_to_create = []
        for job_exe_end in self._job_exe_ends:
            if job_exe_end.job_exe_id not in existing_ids:
                models_to_create.append(job_exe_end)

        # Bulk create new job_exe_end models
        if models_to_create:
            logger.info('Creating %d job_exe_end model(s)', len(models_to_create))
            JobExecutionEnd.objects.bulk_create(models_to_create)

        return True
