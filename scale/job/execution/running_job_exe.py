"""Defines the class that represents running job executions"""
from __future__ import unicode_literals

import threading


class RunningJobExecution(object):
    """This class represents a currently running job execution. This class is thread-safe."""

    def __init__(self, job_exe):
        """Constructor

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, job_type and
            job_type_rev models populated
        :type job_exe: :class:`job.models.JobExecution`
        """

        self._lock = threading.Lock()

        # TODO: Future refactor: replace ScaleJobExecution with the new task system
        from scheduler.scale_job_exe import ScaleJobExecution
        self.scale_job_exe = ScaleJobExecution(job_exe, job_exe.cpus_scheduled, job_exe.mem_scheduled,
                                               job_exe.disk_in_scheduled, job_exe.disk_out_scheduled,
                                               job_exe.disk_total_scheduled)

    def current_task_id(self):
        '''Returns the ID of the current task

        :returns: The ID of the current task, possibly None
        :rtype: str
        '''

        with self._lock:
            return self.scale_job_exe.current_task()

    def is_finished(self):
        """Indicates whether this job execution is finished with all tasks

        :returns: True if all tasks are finished, False otherwise
        :rtype: bool
        """

        with self._lock:
            return self.scale_job_exe.is_finished()

    # TODO: split this into two methods
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
