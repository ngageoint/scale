"""Defines a command message that sets RUNNING status for job models"""
from __future__ import unicode_literals

import logging

from job.models import JobExecutionEnd
from messaging.messages.message import CommandMessage
from util.parse import datetime_to_string, parse_datetime

# This is the maximum number of job models that can fit in one message. This maximum ensures that every message of this
# type is less than 25 KiB long.
MAX_NUM = 100


logger = logging.getLogger(__name__)


class RunningJobs(CommandMessage):
    """Command message that sets RUNNING status for job models
    """

    def __init__(self, started):
        """Constructor

        :param started: The time that the jobs started running
        :type started: :class:`datetime.datetime`
        """

        super(RunningJobs, self).__init__('running_jobs')

        self._count = 0
        self._running_jobs = {}  # {Node ID: [(Job ID, Execution Number)]}
        self._started = started

    def add_running_job(self, job_id, exe_num, node_id):
        """Adds the given running job to this message

        :param job_id: The running job ID
        :type job_id: int
        :param exe_num: The running job's execution number
        :type exe_num: int
        :param node_id: The node ID that the job is running on
        :type node_id: int
        """

        self._count += 1
        job_tuple = (job_id, exe_num)
        if node_id in self._running_jobs:
            self._running_jobs[node_id].append(job_tuple)
        else:
            self._running_jobs[node_id] = [job_tuple]

    def can_fit_more(self):
        """Indicates whether more running jobs can fit in this message

        :return: True if more running jobs can fit, False otherwise
        :rtype: bool
        """

        return self._count < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        node_list = []
        for node_id, job_list in self._running_jobs.items():
            jobs_list = []
            for job_tuple in job_list:
                jobs_list.append({'id': job_tuple[0], 'exe_num': job_tuple[1]})
            node_list.append({'id': node_id, 'jobs': jobs_list})

        return {'started': datetime_to_string(self._started), 'nodes': node_list}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        started = parse_datetime(json_dict['started'])
        message = RunningJobs(started)

        for node_dict in json_dict['nodes']:
            node_id = node_dict['id']
            for job_dict in node_dict['jobs']:
                job_id = job_dict['id']
                exe_num = job_dict['exe_num']
                message.add_running_job(job_id, exe_num, node_id)

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        # TODO: implement

        return True
