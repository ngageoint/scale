"""Defines a command message that resets models due to the scheduler restarting"""
from __future__ import unicode_literals

import logging

from error.models import get_builtin_error
from job.execution.tasks.json.results.task_results import TaskResults
from job.messages.failed_jobs import FailedJob, FailedJobs
from job.messages.job_exe_end import CreateJobExecutionEnd
from job.models import JobExecution
from messaging.messages.message import CommandMessage
from util.parse import datetime_to_string, parse_datetime


logger = logging.getLogger(__name__)


class RestartScheduler(CommandMessage):
    """Command message that resets models due to the scheduler restarting
    """

    def __init__(self):
        """Constructor
        """

        super(RestartScheduler, self).__init__('restart_scheduler')

        self.when = None

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'when': datetime_to_string(self.when)}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = RestartScheduler()
        message.when = parse_datetime(json_dict['when'])
        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        failed_jobs = []
        job_exe_ends = []
        error = get_builtin_error('scheduler-lost')
        task_results = TaskResults(do_validate=False)  # Blank

        # Find executions for unfinished jobs so we can fail them
        for job_exe in JobExecution.objects.get_unfinished_job_exes():
            if job_exe.started < self.when:
                failed_jobs.append(FailedJob(job_exe.job_id, job_exe.exe_num))
                job_exe_ends.append(job_exe.create_job_exe_end_model(task_results, 'FAILED', error.id, self.when))

        # Create messages to fail unfinished jobs and executions
        self._create_failed_jobs_messages(failed_jobs)
        self._create_job_exe_end_messages(job_exe_ends)

        return True

    def _create_failed_jobs_messages(self, failed_jobs):
        """Creates messages to fail the given unfinished jobs

        :param failed_jobs: The unfinished jobs
        :type failed_jobs: list
        """

        error = get_builtin_error('scheduler-lost')

        message = None
        for failed_job in failed_jobs:
            if not message:
                message = FailedJobs()
                message.ended = self.when
            elif not message.can_fit_more():
                self.new_messages.append(message)
                message = FailedJobs()
                message.ended = self.when
            message.add_failed_job(failed_job.job_id, failed_job.exe_num, error.id)
        if message:
            self.new_messages.append(message)

    def _create_job_exe_end_messages(self, job_exe_end_models):
        """Creates messages to create job_exe_end models

        :param job_exe_end_models: The job_exe_end models to create
        :type job_exe_end_models: list
        """

        message = None
        for job_exe_end in job_exe_end_models:
            if not message:
                message = CreateJobExecutionEnd()
            elif not message.can_fit_more():
                self.new_messages.append(message)
                message = CreateJobExecutionEnd()
            message.add_job_exe_end(job_exe_end)
        if message:
            self.new_messages.append(message)
