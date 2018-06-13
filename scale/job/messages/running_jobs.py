"""Defines a command message that sets RUNNING status for job models"""
from __future__ import unicode_literals

import logging

from django.db import transaction
from django.utils.timezone import now

from job.models import Job
from messaging.messages.message import CommandMessage
from util.parse import datetime_to_string, parse_datetime

# This is the maximum number of job models that can fit in one message. This maximum ensures that every message of this
# type is less than 25 KiB long.
MAX_NUM = 100


logger = logging.getLogger(__name__)


def create_running_job_messages(running_job_exes):
    """Creates a list of running job messages for the given running job executions (they must all have the same start
    time)

    :param running_job_exes: The running job executions
    :type running_job_exes: list
    :return: The runnin job messages
    :rtype: list
    """

    messages = []

    message = None
    started = None
    for running_job_exe in running_job_exes:
        if not started:
            started = running_job_exe.started
        if not message:
            message = RunningJobs(started)
        elif not message.can_fit_more():
            messages.append(message)
            message = RunningJobs(started)
        message.add_running_job(running_job_exe.job_id, running_job_exe.exe_num, running_job_exe.node_id)
    if message:
        messages.append(message)

    return messages

class RunningJobs(CommandMessage):
    """Command message that sets RUNNING status for job models
    """

    def __init__(self, started=None):
        """Constructor

        :param started: The time that the jobs started running
        :type started: :class:`datetime.datetime`
        """

        super(RunningJobs, self).__init__('running_jobs')

        if not started:
            started = now()

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

        job_ids = []
        for job_list in self._running_jobs.values():
            for job_tuple in job_list:
                job_ids.append(job_tuple[0])

        with transaction.atomic():
            # Retrieve locked job models
            job_models = {}
            for job in Job.objects.get_locked_jobs(job_ids):
                job_models[job.id] = job

            jobs_to_running = []
            for node_id, job_list in self._running_jobs.items():
                job_ids_for_node_update = []
                for job_tuple in job_list:
                    job_id = job_tuple[0]
                    exe_num = job_tuple[1]
                    job_model = job_models[job_id]
                    if job_model.num_exes != exe_num:
                        continue  # Execution number does not match so this update is out of date, ignore job
                    # Execution numbers match, so this job needs to have its node_id set
                    job_ids_for_node_update.append(job_id)
                    # Job will later be set to RUNNING
                    jobs_to_running.append(job_model)

                # Update jobs for this node
                if job_ids_for_node_update:
                    Job.objects.update_jobs_node(job_ids_for_node_update, node_id, self._started)

            # Update jobs that need status set to RUNNING
            if jobs_to_running:
                running_job_ids = Job.objects.update_jobs_to_running(jobs_to_running, self._started)
                logger.info('Set %d job(s) to RUNNING status', len(running_job_ids))

        # Send messages to update recipe metrics
        from recipe.messages.update_recipe_metrics import create_update_recipe_metrics_messages_from_jobs
        self.new_messages.extend(create_update_recipe_metrics_messages_from_jobs(job_ids))

        return True
