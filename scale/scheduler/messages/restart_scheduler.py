"""Defines a command message that resets models due to the scheduler restarting"""
from __future__ import unicode_literals

import logging

from error.models import get_builtin_error
from job.execution.tasks.json.results.task_results import TaskResults
from job.messages.failed_jobs import create_failed_jobs_messages, FailedJob
from job.messages.job_exe_end import create_job_exe_end_messages
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
                failed_jobs.append(FailedJob(job_exe.job_id, job_exe.exe_num, error.id))
                job_exe_ends.append(job_exe.create_job_exe_end_model(task_results, 'FAILED', error.id, self.when))

        # Create messages to fail unfinished jobs and executions
        if failed_jobs:
            logger.info('Failing %d job(s) that had started but not finished prior to scheduler restart')
            self.new_messages.extend(create_failed_jobs_messages(failed_jobs, self.when))
            self.new_messages.extend(create_job_exe_end_messages(job_exe_ends))

        return True
