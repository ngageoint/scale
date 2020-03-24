"""Defines a command message that creates job_exe_end models"""
from __future__ import unicode_literals

import logging

from job.execution.tasks.json.results.task_results import TaskResults
from job.models import JobExecutionEnd
from messaging.messages.message import CommandMessage
from util.parse import datetime_to_string, parse_datetime
from util.retry import retry_database_query

# This is the maximum number of job_exe_end models that can fit in one message. This maximum ensures that every message
# of this type is less than 25 KiB long.
MAX_NUM = 10


logger = logging.getLogger(__name__)


def create_job_exe_end_messages(job_exe_end_models):
    """Creates messages to create the given job_exe_end models

    :param job_exe_end_models: The job_exe_end models to create
    :type job_exe_end_models: :func:`list`
    :return: The list of messages
    :rtype: :func:`list`
    """

    messages = []

    message = None
    for job_exe_end in job_exe_end_models:
        if not message:
            message = CreateJobExecutionEnd()
        elif not message.can_fit_more():
            messages.append(message)
            message = CreateJobExecutionEnd()
        message.add_job_exe_end(job_exe_end)
    if message:
        messages.append(message)

    return messages


class CreateJobExecutionEnd(CommandMessage):
    """Command message that creates job_exe_end models
    """

    def __init__(self):
        """Constructor
        """

        super(CreateJobExecutionEnd, self).__init__('create_job_exe_ends')

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
                                'task_results': job_exe_end.task_results, 'status': job_exe_end.status,
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
            task_results = TaskResults(job_exe_end_dict['task_results'], do_validate=False)

            job_exe_end.job_exe_id = job_exe_end_dict['id']
            job_exe_end.job_id = job_exe_end_dict['job_id']
            job_exe_end.job_type_id = job_exe_end_dict['job_type_id']
            job_exe_end.exe_num = job_exe_end_dict['exe_num']
            job_exe_end.task_results = job_exe_end_dict['task_results']
            job_exe_end.status = job_exe_end_dict['status']
            job_exe_end.queued = parse_datetime(job_exe_end_dict['queued'])
            job_exe_end.seed_started = task_results.get_task_started('main')
            job_exe_end.seed_ended = task_results.get_task_ended('main')
            job_exe_end.ended = parse_datetime(job_exe_end_dict['ended'])
            if 'error_id' in job_exe_end_dict:
                job_exe_end.error_id = job_exe_end_dict['error_id']
            if 'node_id' in job_exe_end_dict:
                job_exe_end.node_id = job_exe_end_dict['node_id']
            if 'started' in job_exe_end_dict:
                job_exe_end.started = job_exe_end_dict['started']
            message.add_job_exe_end(job_exe_end)

        return message

    @retry_database_query(max_tries=5, base_ms_delay=1000, max_ms_delay=5000)
    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        # See if any of the job_exe_end models already exist
        job_exe_ids = [job_exe_end.job_exe_id for job_exe_end in self._job_exe_ends]
        job_exe_end_qry = JobExecutionEnd.objects.filter(job_exe_id__in=job_exe_ids).only('job_exe_id')
        existing_ids = set(model.job_exe_id for model in job_exe_end_qry)

        # Filter out job_exe_end models that already exist
        models_to_create = []
        for job_exe_end in self._job_exe_ends:
            if job_exe_end.job_exe_id not in existing_ids:
                models_to_create.append(job_exe_end)
                existing_ids.add(job_exe_end.job_exe_id)  # Handles duplicate models in the message

        # Bulk create new job_exe_end models
        if models_to_create:
            logger.info('Creating %d job_exe_end model(s)', len(models_to_create))
            JobExecutionEnd.objects.bulk_create(models_to_create)

        return True
