"""Defines the classes that manages job execution metrics"""
from __future__ import unicode_literals

import datetime
import logging
from collections import namedtuple

from job.execution.configuration.json.exe_config import ExecutionConfiguration
from job.execution.job_exe import RunningJobExecution
from job.models import JobExecutionEnd
from util.retry import retry_database_query

logger = logging.getLogger(__name__)


class JobExeMetrics(object):
    """This class holds metrics for a list of job executions"""

    def __init__(self):
        """Constructor
        """

        self.count = 0

    def add_job_execution(self, job_exe):
        """Adds the given job execution to the metrics

        :param job_exe: The job execution
        :type job_exe: :class:`job.execution.job_exe.RunningJobExecution`
        """

        self.count += 1

    def generate_status_json(self, json_dict):
        """Generates the portion of the status JSON that describes this list of job executions

        :param json_dict: The JSON dict to add these metrics to
        :type json_dict: dict
        """

        json_dict['count'] = self.count

    def remove_job_execution(self, job_exe):
        """Removes the given job execution from the metrics

        :param job_exe: The job execution
        :type job_exe: :class:`job.execution.job_exe.RunningJobExecution`
        """

        self.count -= 1

    def subtract_metrics(self, metrics):
        """Subtracts the given metrics

        :param metrics: The metrics to subtract
        :type metrics: :class:`job.execution.manager.JobExeMetrics`
        """

        self.count -= metrics.count


class JobExeMetricsByType(object):
    """This class holds metrics for job executions grouped by their type"""

    def __init__(self):
        """Constructor
        """

        self.total_count = 0
        self.job_type_metrics = {}  # {Job Type ID: JobExeMetrics}

    def add_job_execution(self, job_exe):
        """Adds the given job execution to the metrics

        :param job_exe: The job execution
        :type job_exe: :class:`job.execution.job_exe.RunningJobExecution`
        """

        self.total_count += 1
        if job_exe.job_type_id not in self.job_type_metrics:
            self.job_type_metrics[job_exe.job_type_id] = JobExeMetrics()
        self.job_type_metrics[job_exe.job_type_id].add_job_execution(job_exe)

    def generate_status_json(self, json_dict):
        """Generates the portion of the status JSON that describes this group of job executions

        :param json_dict: The JSON dict to add these metrics to
        :type json_dict: dict
        """

        json_dict['total'] = self.total_count
        job_type_list = []
        for job_type_id in self.job_type_metrics.keys():
            job_type_dict = {'job_type_id': job_type_id}
            self.job_type_metrics[job_type_id].generate_status_json(job_type_dict)
            job_type_list.append(job_type_dict)
        json_dict['by_job_type'] = job_type_list

    def remove_job_execution(self, job_exe):
        """Removes the given job execution from the metrics

        :param job_exe: The job execution
        :type job_exe: :class:`job.execution.job_exe.RunningJobExecution`
        """

        self.total_count -= 1
        self.job_type_metrics[job_exe.job_type_id].remove_job_execution(job_exe)
        if self.job_type_metrics[job_exe.job_type_id].count == 0:
            del self.job_type_metrics[job_exe.job_type_id]

    def subtract_metrics(self, metrics):
        """Subtracts the given metrics

        :param metrics: The metrics to subtract
        :type metrics: :class:`job.execution.manager.JobExeMetricsByType`
        """

        self.total_count -= metrics.total_count
        for job_type_id in self.job_type_metrics.keys():
            if job_type_id in metrics.job_type_metrics:
                self.job_type_metrics[job_type_id].subtract_metrics(metrics.job_type_metrics[job_type_id])
                if self.job_type_metrics[job_type_id].count == 0:
                    del self.job_type_metrics[job_type_id]


class RunningJobExeMetricsByNode(object):
    """This class holds metrics for running job executions grouped by their node"""

    EMPTY_METRICS = JobExeMetricsByType()

    def __init__(self):
        """Constructor
        """

        self.metrics_by_node = {}  # {Node ID: JobExeMetricsByType}

    def add_job_execution(self, job_exe):
        """Adds the given job execution to the metrics

        :param job_exe: The job execution
        :type job_exe: :class:`job.execution.job_exe.RunningJobExecution`
        """

        if job_exe.node_id not in self.metrics_by_node:
            self.metrics_by_node[job_exe.node_id] = JobExeMetricsByType()
        self.metrics_by_node[job_exe.node_id].add_job_execution(job_exe)

    def generate_status_json(self, nodes_list):
        """Generates the portion of the status JSON that describes these running job executions

        :param nodes_list: The list of nodes within the status JSON
        :type nodes_list: list
        """

        for node_dict in nodes_list:
            node_id = node_dict['id']
            job_exe_dict = node_dict['job_executions']
            running_job_exe_dict = {}
            job_exe_dict['running'] = running_job_exe_dict
            if node_id in self.metrics_by_node:
                self.metrics_by_node[node_id].generate_status_json(running_job_exe_dict)
            else:
                RunningJobExeMetricsByNode.EMPTY_METRICS.generate_status_json(running_job_exe_dict)

    def remove_job_execution(self, job_exe):
        """Removes the given job execution from the metrics

        :param job_exe: The job execution
        :type job_exe: :class:`job.execution.job_exe.RunningJobExecution`
        """

        self.metrics_by_node[job_exe.node_id].remove_job_execution(job_exe)
        if self.metrics_by_node[job_exe.node_id].total_count == 0:
            del self.metrics_by_node[job_exe.node_id]

    def subtract_metrics(self, metrics):
        """Subtracts the given metrics

        :param metrics: The metrics to subtract
        :type metrics: :class:`job.execution.manager.RunningJobExeMetricsByNode`
        """

        for node_id in self.metrics_by_node.keys():
            if node_id in metrics.metrics_by_node:
                self.metrics_by_node[node_id].subtract_metrics(metrics.metrics_by_node[node_id])
                if self.metrics_by_node[node_id].total_count == 0:
                    del self.metrics_by_node[node_id]


class FinishedJobExeMetrics(object):
    """This class holds metrics for finished job executions"""

    def __init__(self):
        """Constructor
        """

        self.completed_metrics = JobExeMetricsByType()
        self.failed_alg_metrics = JobExeMetricsByType()
        self.failed_data_metrics = JobExeMetricsByType()
        self.failed_system_metrics = JobExeMetricsByType()

    @property
    def count(self):
        """Returns the total number of finished job executions

        :returns: The total number of finished job executions
        :rtype: int
        """

        failed_count = self.failed_alg_metrics.total_count
        failed_count += self.failed_data_metrics.total_count
        failed_count += self.failed_system_metrics.total_count
        return self.completed_metrics.total_count + failed_count

    def add_job_execution(self, job_exe):
        """Adds the given job execution to the metrics

        :param job_exe: The job execution
        :type job_exe: :class:`job.execution.job_exe.RunningJobExecution`
        """

        if job_exe.status == 'COMPLETED':
            self.completed_metrics.add_job_execution(job_exe)
        elif job_exe.status == 'FAILED':
            if job_exe.error_category == 'ALGORITHM':
                self.failed_alg_metrics.add_job_execution(job_exe)
            elif job_exe.error_category == 'DATA':
                self.failed_data_metrics.add_job_execution(job_exe)
            elif job_exe.error_category == 'SYSTEM':
                self.failed_system_metrics.add_job_execution(job_exe)

    def generate_status_json(self, json_dict):
        """Generates the portion of the status JSON that describes these finished job executions

        :param json_dict: The JSON dict to add these metrics to
        :type json_dict: dict
        """

        completed_dict = {}
        self.completed_metrics.generate_status_json(completed_dict)

        alg_dict = {}
        data_dict = {}
        system_dict = {}
        failed_count = self.failed_alg_metrics.total_count
        failed_count += self.failed_data_metrics.total_count
        failed_count += self.failed_system_metrics.total_count
        self.failed_alg_metrics.generate_status_json(alg_dict)
        self.failed_data_metrics.generate_status_json(data_dict)
        self.failed_system_metrics.generate_status_json(system_dict)
        failed_dict = {'total': failed_count, 'algorithm': alg_dict, 'data': data_dict, 'system': system_dict}

        json_dict['completed'] = completed_dict
        json_dict['failed'] = failed_dict

    def subtract_metrics(self, metrics):
        """Subtracts the given metrics

        :param metrics: The metrics to subtract
        :type metrics: :class:`job.execution.manager.FinishedJobExeMetrics`
        """

        self.completed_metrics.subtract_metrics(metrics.completed_metrics)
        self.failed_alg_metrics.subtract_metrics(metrics.failed_alg_metrics)
        self.failed_data_metrics.subtract_metrics(metrics.failed_data_metrics)
        self.failed_system_metrics.subtract_metrics(metrics.failed_system_metrics)


class FinishedJobExeMetricsByNode(object):
    """This class holds metrics for finished job executions, grouped by node"""

    EMPTY_METRICS = FinishedJobExeMetrics()

    def __init__(self):
        """Constructor
        """

        self.metrics_by_node = {}  # {Node ID: FinishedJobExeMetrics}

    def add_job_execution(self, job_exe):
        """Adds the given job execution to the metrics

        :param job_exe: The job execution
        :type job_exe: :class:`job.execution.job_exe.RunningJobExecution`
        """

        if job_exe.node_id not in self.metrics_by_node:
            self.metrics_by_node[job_exe.node_id] = FinishedJobExeMetrics()
        self.metrics_by_node[job_exe.node_id].add_job_execution(job_exe)

    def generate_status_json(self, nodes_list):
        """Generates the portion of the status JSON that describes these finished job executions

        :param nodes_list: The list of nodes within the status JSON
        :type nodes_list: list
        """

        for node_dict in nodes_list:
            node_id = node_dict['id']
            job_exe_dict = node_dict['job_executions']
            if node_id in self.metrics_by_node:
                self.metrics_by_node[node_id].generate_status_json(job_exe_dict)
            else:
                FinishedJobExeMetricsByNode.EMPTY_METRICS.generate_status_json(job_exe_dict)

    def subtract_metrics(self, metrics):
        """Subtracts the given metrics

        :param metrics: The metrics to subtract
        :type metrics: :class:`job.execution.manager.FinishedJobExeMetricsByNode`
        """

        for node_id in self.metrics_by_node.keys():
            if node_id in metrics.metrics_by_node:
                self.metrics_by_node[node_id].subtract_metrics(metrics.metrics_by_node[node_id])
                if self.metrics_by_node[node_id].count == 0:
                    del self.metrics_by_node[node_id]


class FinishedJobExeMetricsOverTime(object):
    """This class holds metrics for finished job executions, grouped and sorted into time blocks"""

    TOTAL_TIME_PERIOD = datetime.timedelta(hours=3)
    BLOCK_LENGTH = datetime.timedelta(minutes=5)
    TIME_BLOCK = namedtuple('TIME_BLOCK', ['start', 'end', 'metrics'])

    def __init__(self, when):
        """Constructor

        :param when: The current time
        :type when: :class:`datetime.datetime`
        """

        # Create a time-ordered list of time blocks, each with duration BLOCK_LENGTH, going back from now to cover a
        # period of time of length TOTAL_TIME_PERIOD
        self.time_blocks = []
        end = when
        start_of_total_period = end - FinishedJobExeMetricsOverTime.TOTAL_TIME_PERIOD
        while True:
            start = end - FinishedJobExeMetricsOverTime.BLOCK_LENGTH
            time_block = FinishedJobExeMetricsOverTime.TIME_BLOCK(start, end, FinishedJobExeMetricsByNode())
            self.time_blocks.insert(0, time_block)
            end = start
            if end <= start_of_total_period:
                break

    def add_job_execution(self, job_exe):
        """Adds the given job execution to the metrics

        :param job_exe: The job execution
        :type job_exe: :class:`job.execution.job_exe.RunningJobExecution`
        """

        when = job_exe.finished
        index = len(self.time_blocks) - 1  # Start at last time block, most likely to be correct one
        while True:
            time_block = self.time_blocks[index]
            if time_block.end <= when:
                # Job execution is later than last time block, create a new one
                start = time_block.end
                end = start + FinishedJobExeMetricsOverTime.BLOCK_LENGTH
                new_time_block = FinishedJobExeMetricsOverTime.TIME_BLOCK(start, end, FinishedJobExeMetricsByNode())
                self.time_blocks.append(new_time_block)
                index += 1
            elif time_block.start <= when < time_block.end:
                # Job execution fits in this time block, so add it
                time_block.metrics.add_job_execution(job_exe)
                break
            elif when < time_block.start:
                # Job execution is earlier than this time block, so move to earlier block
                index -= 1
                if index < 0:  # Job execution is before any time blocks, ignore it
                    logger.error('Logic bug: Job execution finished before our metrics time period')
                    break

    def update_to_now(self, when):
        """Updates the metrics to now by removing any time blocks that are older than our time period and creates any
        needed new blocks

        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: The list of removed metrics classes for old time blocks
        :rtype: [:class:`job.execution.metrics.FinishedJobExeMetricsByNode`]
        """

        start_of_total_period = when - FinishedJobExeMetricsOverTime.TOTAL_TIME_PERIOD
        results = []

        # Add any needed new time blocks
        while True:
            if self.time_blocks[-1].end <= when:
                start = self.time_blocks[-1].end
                end = start + FinishedJobExeMetricsOverTime.BLOCK_LENGTH
                new_time_block = FinishedJobExeMetricsOverTime.TIME_BLOCK(start, end, FinishedJobExeMetricsByNode())
                self.time_blocks.append(new_time_block)
            else:
                break

        # Remove any time blocks from front of list that are too old and outside the time period
        while True:
            if self.time_blocks[0].end < start_of_total_period:
                results.append(self.time_blocks[0].metrics)
                self.time_blocks.pop(0)
            else:
                break

        return results


class TotalJobExeMetrics(object):
    """This class handles all real-time metrics for job executions"""

    def __init__(self, when):
        """Constructor

        :param when: The current time
        :type when: :class:`datetime.datetime`
        """

        self._finished_metrics = FinishedJobExeMetricsByNode()
        self._finished_metrics_over_time = FinishedJobExeMetricsOverTime(when)
        self._running_metrics = RunningJobExeMetricsByNode()

    def add_running_job_exes(self, job_exes):
        """Adds newly scheduled running job executions to the metrics

        :param job_exes: A list of the running job executions to add
        :type job_exes: [:class:`job.execution.job_exe.RunningJobExecution`]
        """

        for job_exe in job_exes:
            self._running_metrics.add_job_execution(job_exe)

    def generate_status_json(self, nodes_list, when):
        """Generates the portion of the status JSON that describes the job execution metrics

        :param nodes_list: The list of nodes within the status JSON
        :type nodes_list: list
        :param when: The current time
        :type when: :class:`datetime.datetime`
        """

        # Remove any old metrics that have fallen outside of the time period
        for old_metrics in self._finished_metrics_over_time.update_to_now(when):
            self._finished_metrics.subtract_metrics(old_metrics)

        for node_dict in nodes_list:
            node_dict['job_executions'] = {}
        self._running_metrics.generate_status_json(nodes_list)
        self._finished_metrics.generate_status_json(nodes_list)

    @retry_database_query
    def init_with_database(self):
        """Initializes the job execution metrics with the execution history from the database
        """

        oldest_time = self._finished_metrics_over_time.time_blocks[0].start
        blank_config = ExecutionConfiguration()
        for job_exe_end in JobExecutionEnd.objects.get_recent_job_exe_end_metrics(oldest_time):
            running_job_exe = RunningJobExecution('', job_exe_end.job_exe, job_exe_end.job_type, blank_config, 0)
            running_job_exe._set_final_status(job_exe_end.status, job_exe_end.ended, job_exe_end.error)
            self._finished_metrics.add_job_execution(running_job_exe)
            self._finished_metrics_over_time.add_job_execution(running_job_exe)

    def job_exe_finished(self, job_exe):
        """Handles a running job execution that has finished

        :param job_exe: The finished job execution
        :type job_exe: :class:`job.execution.job_exe.RunningJobExecution`
        """

        self._finished_metrics.add_job_execution(job_exe)
        self._finished_metrics_over_time.add_job_execution(job_exe)
        self._running_metrics.remove_job_execution(job_exe)
