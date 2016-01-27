'''Scale Job Execution handles running Scale jobs within Mesos'''
from __future__ import unicode_literals

import logging
import os
import re
import subprocess
from datetime import datetime, timedelta

from django.db import transaction
from django.utils.timezone import now, utc

from error.models import Error
from job import settings
from job.execution.file_system import get_job_exe_input_dir, get_job_exe_output_dir
from job.management.commands.scale_post_steps import EXIT_CODE_DICT as POST_EXIT_CODE_DICT
from job.management.commands.scale_pre_steps import EXIT_CODE_DICT as PRE_EXIT_CODE_DICT
from job.models import JobExecution
from mesos_api.api import get_slave_task_directory, get_slave_task_run_id, get_slave_task_url, get_slave_task_file
from queue.models import Queue
from scheduler.scheduler_errors import get_mesos_error, get_timeout_error
from scheduler.models import Scheduler

logger = logging.getLogger(__name__)

try:
    from mesos.interface import mesos_pb2
    logger.info('Successfully imported native Mesos bindings')
except ImportError:
    logger.info('No native Mesos bindings, falling back to stubs')
    import mesos_api.mesos_pb2 as mesos_pb2

EPOCH = datetime.utcfromtimestamp(0).replace(tzinfo=utc)
EXIT_CODE_PATTERN = re.compile(r'Command exited with status ([\-0-9]+)')


class ScaleJobExecution(object):
    '''This class encapsulates the information about a Scale job execution that the scheduler needs to perform Mesos
    task scheduling.
    '''

    @staticmethod
    def get_job_exe_id(task_id):
        '''Returns the job execution ID for the given task ID

        :param task_id: The task ID
        :type task_id: str
        :returns: The job execution ID
        :rtype: int
        '''

        return int(task_id.split('_')[0])

    def __repr__(self):
        return "<ScaleJobExecution: %r %r>" % (self.job_exe_id, self._cached_job_type_name)

    def __init__(self, job_exe, cpus, mem, disk_in, disk_out, disk_total):
        '''Constructor

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, job_type and
            job_type_rev models populated
        :type job_exe: :class:`job.models.JobExecution`
        :param cpus: The number of CPUs to schedule for the job execution
        :type cpus: float
        :param mem: The amount of memory in MiB to schedule for the job execution
        :type mem: float
        :param disk_in: The amount of disk space for input files in MiB to schedule for the job execution
        :type disk_in: float
        :param disk_out: The amount of disk space for temp files and products in MiB to schedule for the job execution
        :type disk_out: float
        :param disk_total: The total amount of disk space in MiB to schedule for the job execution
        :type disk_total: float
        '''

        self.job_exe_id = job_exe.id
        self.cpus = cpus
        self.mem = mem
        self.disk_in = disk_in
        self.disk_out = disk_out
        self.disk_total = disk_total
        self.failed = False

        self.timed_out = False

        self.current_task_id = None
        self.current_task_stdout_url = None
        self.current_task_stderr_url = None

        # Caching these since they should not change for a given execution
        self._cached_job_interface = job_exe.get_job_interface()
        self._cached_node = job_exe.node
        self._cached_job_type_name = job_exe.get_job_type_name()

        with transaction.atomic():
            job_exe = JobExecution.objects.select_for_update().defer('stdout', 'stderr').get(pk=self.job_exe_id)
            self.remaining_task_ids = []
            if not job_exe.is_system():
                pre_task_id = '%i_pre' % job_exe.id
                self.remaining_task_ids.append(pre_task_id)
                job_exe.pre_task_id = pre_task_id
            job_task_id = '%i_job' % job_exe.id
            self.remaining_task_ids.append(job_task_id)
            if not job_exe.is_system():
                post_task_id = '%i_post' % job_exe.id
                self.remaining_task_ids.append(post_task_id)
                job_exe.post_task_id = post_task_id
            job_exe.save()

    def current_task(self):
        '''Returns the ID of the current task

        :returns: The ID of the current task, possibly None
        :rtype: str
        '''

        return self.current_task_id

    def get_current_task_resources(self):
        '''Returns the resources scheduled for the current task

        :returns: A tuple of the CPU, memory, and disk resources
        :rtype: (float, float, float)
        '''

        return (self.cpus, self.mem, self._get_task_disk_required(self.current_task_id))

    def is_finished(self):
        '''Returns whether this job execution is finished with all Mesos tasks

        :returns: True if all tasks are finished, False otherwise
        :rtype: bool
        '''

        return self.current_task_id is None and not self.remaining_task_ids

    def is_next_task_ready(self, cpus, mem, disk):
        '''Returns whether the next Mesos task for this job execution is ready and able to run with the given resources

        :param cpus: The number of CPUs available
        :type cpus: float
        :param mem: The amount of memory in MiB available
        :type mem: float
        :param disk: The amount of disk space in MiB available
        :type disk: float
        :returns: True if the next task is ready, False otherwise
        :rtype: bool
        '''

        if not self.current_task_id is None:
            return False

        enough_cpus = cpus >= self.cpus
        enough_mem = mem >= self.mem
        if not self.remaining_task_ids:
            enough_disk = True
        else:
            enough_disk = disk >= self._get_task_disk_required(self.remaining_task_ids[0])

        return enough_cpus and enough_mem and enough_disk

    def start_next_task(self):
        '''Returns the next Mesos task to be scheduled

        :returns: The next Mesos task to schedule
        :rtype: :class:`mesos_pb2.TaskInfo`
        '''

        if not self.current_task_id is None:
            raise Exception('Already working on a task')

        if not self.remaining_task_ids:
            raise Exception('No more tasks to start')

        self.current_task_id = self.remaining_task_ids.pop(0)

        return self._create_current_task()

    def task_completed(self, task_id, status):
        '''Indicates that a Mesos task for this job execution has completed

        :param task_id: The ID of the task that was completed
        :type task_id: str
        :param status: The task status
        :type status: :class:`mesos_pb2.TaskStatus`
        '''

        if not self.current_task_id == task_id:
            return

        when_completed = EPOCH + timedelta(seconds=status.timestamp)
        exit_code = self._parse_exit_code(status)

        stdout = None
        stderr = None
        log_start_time = now()
        try:
            node = self._cached_node
            task_dir = get_slave_task_directory(node.hostname, node.port, self.current_task_id)
            mesos_run_id = get_slave_task_run_id(node.hostname, node.port, self.current_task_id)

            stdout = get_slave_task_file(node.hostname, node.port, task_dir, 'stdout')
            stderr = get_slave_task_file(node.hostname, node.port, task_dir, 'stderr')
        except Exception:
            logger.error('Error getting stdout/stderr for %s', self.current_task_id)
        log_end_time = now()
        logger.debug('Time to pull logs for completed task: %s', str(log_end_time - log_start_time))

        query_start_time = now()

        if self._is_current_task_pre():
            JobExecution.objects.pre_steps_completed(self.job_exe_id, when_completed, exit_code, stdout, stderr)
        elif self._is_current_task_job():
            JobExecution.objects.job_completed(self.job_exe_id, when_completed, exit_code, stdout, stderr, mesos_run_id)
        elif self._is_current_task_post():
            JobExecution.objects.post_steps_completed(self.job_exe_id, when_completed, exit_code, stdout, stderr)

        JobExecution.objects.set_log_urls(self.job_exe_id, None, None)

        # Only successfully completed if there are no more tasks and we never failed along the way
        if not self.remaining_task_ids and not self.failed:
            Queue.objects.handle_job_completion(self.job_exe_id, when_completed)
        self.current_task_id = None
        self.current_task_stdout_url = None
        self.current_task_stderr_url = None

        query_end_time = now()
        logger.debug('Time to do queries for completed task: %s', str(query_end_time - query_start_time))

    def task_failed(self, task_id, status):
        '''Indicates that a Mesos task for this job execution has failed

        :param task_id: The ID of the task that failed
        :type task_id: str
        :param status: The task status
        :type status: :class:`mesos_pb2.TaskStatus`
        '''

        if not self.current_task_id == task_id:
            return

        job_exe = JobExecution.objects.get_job_exe_with_job_and_job_type(self.job_exe_id)

        stdout = None
        stderr = None
        node = None
        if status.state != mesos_pb2.TASK_LOST:
            try:
                node = self._cached_node
                task_dir = get_slave_task_directory(node.hostname, node.port, self.current_task_id)
                stdout = get_slave_task_file(node.hostname, node.port, task_dir, 'stdout')
                stderr = get_slave_task_file(node.hostname, node.port, task_dir, 'stderr')
            except Exception:
                logger.error('Error getting stdout/stderr for %s', self.current_task_id)

        self.failed = True
        error = None
        if status.state == mesos_pb2.TASK_LOST:
            error = get_mesos_error()
        if status.state == mesos_pb2.TASK_KILLED and self.timed_out:
            error = get_timeout_error()
        when_failed = EPOCH + timedelta(seconds=status.timestamp)

        exit_code = self._parse_exit_code(status)
        if self._is_current_task_pre():
            # Check scale_pre_steps command to see if exit code maps to a specific error
            if exit_code in PRE_EXIT_CODE_DICT:
                error = PRE_EXIT_CODE_DICT[exit_code]()
            JobExecution.objects.pre_steps_failed(self.job_exe_id, when_failed, exit_code, stdout, stderr)
        elif self._is_current_task_job():
            # Do error mapping here to determine error
            error = job_exe.get_error_interface().get_error(exit_code)
            JobExecution.objects.job_failed(self.job_exe_id, when_failed, exit_code, stdout, stderr)
        elif self._is_current_task_post():
            # Check scale_post_steps command to see if exit code maps to a specific error
            if exit_code in POST_EXIT_CODE_DICT:
                error = POST_EXIT_CODE_DICT[exit_code]()
            JobExecution.objects.post_steps_failed(self.job_exe_id, when_failed, exit_code, stdout, stderr)

        if not error:
            error = Error.objects.get_unknown_error()
        Queue.objects.handle_job_failure(self.job_exe_id, when_failed, error)

        # Check for a high number of system errors and decide if we should pause the node
        if error.category == 'SYSTEM' and job_exe.job.num_exes >= job_exe.job.max_tries and node is not None and not node.is_paused:
            # search Job.objects. for the number of system failures in the past (configurable) 1 minute
            # if (configurable) 5 or more have occurred, pause the node
            node_error_period = Scheduler.objects.first().node_error_period
            if node_error_period > 0:
                check_time = datetime.utcnow() - timedelta(minutes=node_error_period)
                # find out how many jobs have recently failed on this node with a system error
                num_node_errors = JobExecution.objects.select_related('error', 'node').filter(
                    status='FAILED', error__category='SYSTEM', ended__gte=check_time, node=node).distinct('job').count()
                max_node_errors = Scheduler.objects.first().max_node_errors
                if num_node_errors >= max_node_errors:
                    logger.warning('%s failed %d jobs in %d minutes, pausing the host' % (node.hostname, num_node_errors, node_error_period))
                    with transaction.atomic():
                        node.is_paused = True
                        node.is_paused_errors = True
                        node.pause_reason = "System Failure Rate Too High"
                        node.save()

        # Remove all remaining tasks
        self.remaining_task_ids = []

        self.current_task_id = None
        self.current_task_stdout_url = None
        self.current_task_stderr_url = None
        JobExecution.objects.set_log_urls(self.job_exe_id, None, None)

    def task_running(self, task_id, status):
        '''Indicates that a Mesos task for this job execution has started running

        :param task_id: The ID of the task that has started running
        :type task_id: str
        :param status: The task status
        :type status: :class:`mesos_pb2.TaskStatus`
        '''

        if not self.current_task_id == task_id:
            return

        when_started = EPOCH + timedelta(seconds=status.timestamp)

        log_start_time = now()
        # update the stdout/stderr URLs for log access
        try:
            node = self._cached_node
            task_dir = get_slave_task_directory(node.hostname, node.port, self.current_task_id)
            self.current_task_stdout_url = get_slave_task_url(node.hostname, node.port, task_dir, 'stdout')
            self.current_task_stderr_url = get_slave_task_url(node.hostname, node.port, task_dir, 'stderr')
        except Exception:
            logger.exception('Error getting stdout/stderr for %s', self.current_task_id)
        log_end_time = now()
        logger.debug('Time to pull log URLs for running task: %s', str(log_end_time - log_start_time))

        query_start_time = now()
        if self._is_current_task_pre():
            JobExecution.objects.pre_steps_started(self.job_exe_id, when_started)
        elif self._is_current_task_job():
            JobExecution.objects.job_started(self.job_exe_id, when_started)
        elif self._is_current_task_post():
            JobExecution.objects.post_steps_started(self.job_exe_id, when_started)

        # write stdout/stderr URLs to the database
        JobExecution.objects.set_log_urls(self.job_exe_id, self.current_task_stdout_url, self.current_task_stderr_url)

        query_end_time = now()
        logger.debug('Time to do queries for running task: %s', str(query_end_time - query_start_time))

    def _create_base_task(self, task_name):
        '''Creates and returns a base Mesos task

        :param task_name: The task name
        :type task_name: str
        :returns: The base Mesos task
        :rtype: :class:`mesos_pb2.TaskInfo`
        '''

        task_cpus, task_mem, task_disk = self.get_current_task_resources()

        task = mesos_pb2.TaskInfo()
        task.task_id.value = self.current_task_id
        task.slave_id.value = self._cached_node.slave_id
        task.name = task_name

        if task_cpus > 0:
            cpus = task.resources.add()
            cpus.name = 'cpus'
            cpus.type = mesos_pb2.Value.SCALAR
            cpus.scalar.value = task_cpus

        if task_mem > 0:
            mem = task.resources.add()
            mem.name = 'mem'
            mem.type = mesos_pb2.Value.SCALAR
            mem.scalar.value = task_mem

        if task_disk > 0:
            disk = task.resources.add()
            disk.name = 'disk'
            disk.type = mesos_pb2.Value.SCALAR
            disk.scalar.value = task_disk

        return task

    def _create_docker_task(self, job_exe):
        '''Creates and returns a docker task for this job execution

        :param job_exe: The JobExecution that we are creating a task for
        :type job_exe: :class:`job.models.JobExecution`
        returns: The Docker Mesos task
        rtype: :class:`mesos_pb2.TaskInfo`
        '''
        input_dir = get_job_exe_input_dir(self.job_exe_id)
        output_dir = get_job_exe_output_dir(self.job_exe_id)

        task_name = 'Job Execution %i (%s)' % (self.job_exe_id, self._cached_job_type_name)
        task = self._create_base_task(task_name)
        task.container.type = mesos_pb2.ContainerInfo.DOCKER

        docker_image = job_exe.get_docker_image()
        command = job_exe.get_job_interface().get_command()
        command_arguments = job_exe.command_arguments
        assert docker_image is not None

        task.container.docker.image = docker_image

        # If the docker container is to run in privileged mode,
        # set the 'privileged' boolean attribute.
        if job_exe.is_docker_privileged():
            task.container.docker.privileged = True

        # TODO: Determine whether or not there is an entry point within
        # the docker image in order to pass in the docker container
        # command arguments correctly.
        # Right now we assume an entry point
        task.command.shell = False

        # parse through the docker arguments and add them
        # to the CommandInfo 'arguments' list
        arguments = command_arguments.split(" ")
        for argument in arguments:
            task.command.arguments.append(argument)

        input_vol = task.container.docker.parameters.add()
        input_vol.key = "volume"
        input_vol.value = "%s:%s:ro" % (input_dir, input_dir)

        output_vol = task.container.docker.parameters.add()
        output_vol.key = "volume"
        output_vol.value = "%s:%s:rw" % (output_dir, output_dir)

        task.container.docker.network = mesos_pb2.ContainerInfo.DockerInfo.Network.Value('BRIDGE')

        logger.info("about to launch docker (assuming an entry point) with:")
        logger.info("arguments:%s", task.command.arguments)
        logger.info("input_vol:%s", input_vol.value)
        logger.info("output_vol:%s", output_vol.value)

        return task

    def _invoke_docker(self, command, arguments=[], stdout=None, stderr=None):
        """
        Invoke the docker command line tool. This function returns a tuple that
        contains (stdout, stderr, return_code)
        """

        # build up the docker command
        invoke = ["docker"]

        # Include any global docker arguments
        docker_args = os.environ.get("CONTAINERIZER_DOCKER_ARGS")
        if docker_args:
            invoke.extend(docker_args.split(" "))

        # add the command and arguments
        invoke.append(command)
        invoke.extend(arguments)

        logger.info("Invoking docker with %r", invoke)

        proc = subprocess.Popen(invoke, stdout=stdout, stderr=stderr)
        return proc.stdout, proc.stderr, proc.wait()

    def _create_command_task(self, job_exe):
        '''Creates and returns a command line task for this job execution

        :param job_exe: The JobExecution that we are creating a task for
        :type job_exe: :class:`job.models.JobExecution`
        :returns: The command line Mesos task
        :rtype: :class:`mesos_pb2.TaskInfo`
        '''

        task_name = 'Job Execution %i (%s)' % (self.job_exe_id, self._cached_job_type_name)
        task = self._create_base_task(task_name)

        command = job_exe.get_job_interface().get_command()
        command = command + ' ' + job_exe.command_arguments

        if job_exe.is_system():
            command = '%s %s %s' % (settings.settings.PYTHON_EXECUTABLE, settings.settings.MANAGE_FILE, command)
        task.command.value = command

        return task

    def _create_current_task(self):
        '''Creates and returns the current Mesos task to be scheduled

        :returns: The current Mesos task
        :rtype: :class:`mesos_pb2.TaskInfo`
        '''

        job_exe = JobExecution.objects.get_job_exe_with_job_and_job_type(self.job_exe_id)

        if self._is_current_task_pre():
            return self._create_pre_task()
        elif self._is_current_task_post():
            return self._create_post_task()

        if job_exe.uses_docker():
            return self._create_docker_task(job_exe)
        else:
            return self._create_command_task(job_exe)

    def _create_post_task(self):
        '''Creates and returns a post-job task for this job execution

        returns: The current post-job Mesos task
        rtype: :class:`mesos_pb2.TaskInfo`
        '''

        task_name = 'Job Execution (Post) %i (%s)' % (self.job_exe_id, self._cached_job_type_name)
        task = self._create_base_task(task_name)

        system_cmd = '%s %s ' % (settings.settings.PYTHON_EXECUTABLE, settings.settings.MANAGE_FILE)

        post_job_cmd = 'scale_post_steps -i %i' % self.job_exe_id
        task.command.value = system_cmd + post_job_cmd

        return task

    def _create_pre_task(self):
        '''Creates and returns a pre-job task for this job execution

        returns: The current pre-job Mesos task
        rtype: :class:`mesos_pb2.TaskInfo`
        '''

        task_name = 'Job Execution (Pre) %i (%s)' % (self.job_exe_id, self._cached_job_type_name)
        task = self._create_base_task(task_name)

        system_cmd = '%s %s ' % (settings.settings.PYTHON_EXECUTABLE, settings.settings.MANAGE_FILE)
        pre_job_cmd = 'scale_pre_steps -i %i' % self.job_exe_id
        task.command.value = system_cmd + pre_job_cmd

        return task

    def _get_task_disk_required(self, task_id):
        '''Returns the disk space in MiB required for the given task

        :param task_id: The task ID
        :type task_id: str
        :returns: The required disk space in MiB
        :rtype: float
        '''

        if 'pre' in task_id:
            return self.disk_total
        elif 'job' in task_id:
            return self.disk_out
        return 0

    def _is_current_task_job(self):
        '''Indicates if the current task is the actual job

        :returns: True if the current task is the actual job, False otherwise
        :rtype: bool
        '''

        return self.current_task_id and 'job' in self.current_task_id

    def _is_current_task_post(self):
        '''Indicates if the current task is a post-job task

        :returns: True if the current task is a post-job task, False otherwise
        :rtype: bool
        '''

        return self.current_task_id and 'post' in self.current_task_id

    def _is_current_task_pre(self):
        '''Indicates if the current task is a pre-job task

        :returns: True if the current task is a pre-job task, False otherwise
        :rtype: bool
        '''

        return self.current_task_id and 'pre' in self.current_task_id

    def _parse_exit_code(self, status):
        '''Parses and returns an exit code from the task status, returns None
        if no exit code can be parsed

        :param status: The task status
        :type status: :class:`mesos_pb2.TaskStatus`
        :returns: The exit code, possibly None
        :rtype: int
        '''

        exit_code = None

        try:
            match = EXIT_CODE_PATTERN.search(status.message)
            if match:
                exit_code = int(match.group(1))
        except Exception:
            logger.exception('Error parsing task exit code')

        return exit_code
