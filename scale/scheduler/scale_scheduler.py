'''The Scale mesos framework scheduler.
This module is responsible for adding mesos tasks based on available resources'''
from __future__ import unicode_literals

import copy
import logging
import math
import os
import sys
import threading
import time

from django.conf import settings
from django.utils.timezone import now

from job.models import JobExecution
from mesos_api import api
from mesos_api import utils
from node.models import Node
from queue.models import Queue
from scheduler import models
from scheduler.initialize import initialize_system
from scheduler.scale_job_exe import ScaleJobExecution
from scheduler.scheduler_errors import get_node_lost_error, get_scheduler_error, get_timeout_error


logger = logging.getLogger(__name__)


try:
    from mesos.interface import Scheduler
    from mesos.interface import mesos_pb2
    logger.info('Successfully imported native Mesos bindings')
except ImportError:
    logger.info('No native Mesos bindings, falling back to stubs')
    from mesos_api.mesos import Scheduler
    import mesos_api.mesos_pb2 as mesos_pb2


def connect_remote_debug():
    '''Connects to a pydev remote debug server'''
    pydev_src = os.getenv('PYDEV_SRC')
    remote_debug_host = os.getenv('REMOTE_DEBUG_HOST')
    if pydev_src and remote_debug_host:
        if pydev_src not in sys.path:
            sys.path.append(pydev_src)
        try:
            import pydevd
            logger.info('attempting to connect debugging to Remote Host:%s', remote_debug_host)
            pydevd.settrace(remote_debug_host, suspend=False)
            logger.info('connected to Remote Host')
        except:
            logger.exception('connecting to remote debug server failed')


class ScaleOffer(object):
    '''Represents Mesos resources that have been offered to Scale and are
    currently being scheduled.
    '''

    def __init__(self, offer, node):
        '''Constructor

        :param offer: The resource offer from Mesos
        :type offer: :class:`mesos_pb2.Offer`
        :param node: The node for the offer
        :type node: :class:`node.models.Node`
        '''

        self.offer_id = offer.id
        self.offer_id_str = offer.id.value
        self.hostname = offer.hostname
        self.slave_id = offer.slave_id.value
        self.node_id = node.id
        resources = offer.resources
        self.disk = 0
        self.mem = 0
        self.cpus = 0
        for resource in resources:
            if resource.name == 'disk':
                self.disk = resource.scalar.value
            elif resource.name == 'mem':
                self.mem = resource.scalar.value
            elif resource.name == 'cpus':
                self.cpus = resource.scalar.value
        self.tasks = []

    @property
    def node(self):
        try:
            return Node.objects.get(id=self.node_id)
        except Exception, ex:
            logger.exception('Invalid node id %r', self.node_id)
            raise ex

    @property
    def can_run_new_jobs(self):
        '''Is the node attached to this offer eligable to run new jobs
        or can it only finish existing jobs?

        :rval: True if new jobs can be scheduled, False otherwise.
        :rtype: bool
        '''
        node = Node.objects.get(id=self.node_id)
        return not node.is_paused and node.is_active

    def add_task(self, task, task_cpus, task_mem, task_disk):
        '''Adds the given task to this offer

        :param task: The task to add
        :type task: :class:`mesos_pb2.TaskInfo`
        :param task_cpus: The number of CPUs needed for the task
        :type task_cpus: float
        :param task_mem: The amount of memory in MiB needed for the task
        :type task_mem: float
        :param task_disk: The amount of disk space in MiB needed for the task
        :type task_disk: float
        '''

        if task_cpus > self.cpus:
            raise Exception('Task requires more CPUs than available')
        if task_mem > self.mem:
            raise Exception('Task requires more memory than available')
        if task_disk > self.disk:
            raise Exception('Task requires more disk than available')

        self.cpus = self.cpus - task_cpus
        self.mem = self.mem - task_mem
        self.disk = self.disk - task_disk
        self.tasks.append(task)


class ScaleScheduler(Scheduler):
    '''Mesos scheduler for the Scale framework
    '''

    def __init__(self, executor):
        '''Constructor
        :param executor: The executor to use for launching tasks
        :type executor: :class:`mesos_pb2.ExecutorInfo`
        '''

        self.debug = settings.DEBUG
        self.executor = executor
        self.framework_id = None
        self.master_hostname = None
        self.master_port = None
        self.driver = None

        # Keeps track of the current Scale job executions in 'RUNNING' status
        # Stored as {slave ID: list of ScaleJobExecution}
        self.current_jobs = {}
        self.current_jobs_lock = threading.Lock()

        # Keeps track of node IDs by slave ID
        self.node_ids = {}

        # Reconciliation set contains IDs of all tasks to reconcile
        self.recon_set = set()
        self.recon_lock = threading.Lock()

        # Start up background thread to perform reconciliation
        target = self._perform_reconciliation
        self.recon_running = True
        self.recon_thread = threading.Thread(target=target)
        self.recon_thread.daemon = True
        self.recon_thread.start()

        # Start a background thread to sync updates from the database
        target = self._sync_with_database_thread
        self.sync_database_running = True
        self.sync_database_thread = threading.Thread(target=target)
        self.sync_database_thread.daemon = True
        self.sync_database_thread.start()

    def registered(self, driver, frameworkId, masterInfo):
        '''
        Invoked when the scheduler successfully registers with a Mesos master.
        It is called with the frameworkId, a unique ID generated by the
        master, and the masterInfo which is information about the master
        itself.

        See documentation for :meth:`mesos_api.mesos.Scheduler.registered`.
        '''

        if self.debug:
            connect_remote_debug()

        logger.info('Scale scheduler registered as framework %s with Mesos master at %s:%i',
                    frameworkId.value, masterInfo.hostname, masterInfo.port)

        self.driver = driver
        self.framework_id = frameworkId.value
        self.master_hostname = masterInfo.hostname
        self.master_port = masterInfo.port
        models.Scheduler.objects.update_master(self.master_hostname, self.master_port)

        try:
            initialize_system()
        except Exception as ex:
            logger.exception('Failed to perform system initialization, killing scheduler')
            raise ex

        try:
            self._reconcile_running_jobs()
        except Exception as ex:
            logger.exception('Failed to query running jobs for reconciliation, killing scheduler')
            raise ex

    def reregistered(self, driver, masterInfo):
        '''
        Invoked when the scheduler re-registers with a newly elected Mesos
        master.  This is only called when the scheduler has previously been
        registered.  masterInfo contains information about the newly elected
        master.

        See documentation for :meth:`mesos_api.mesos.Scheduler.reregistered`.
        '''

        if self.debug:
            connect_remote_debug()

        logger.info('Scale scheduler re-registered with Mesos master at %s:%i', masterInfo.hostname, masterInfo.port)
        self.driver = driver
        self.master_hostname = masterInfo.hostname
        self.master_port = masterInfo.port
        models.Scheduler.objects.update_master(self.master_hostname, self.master_port)

        try:
            self._reconcile_running_jobs()
        except Exception as ex:
            logger.exception('Failed to query running jobs for reconciliation, killing scheduler')
            raise ex

    def disconnected(self, driver):
        '''
        Invoked when the scheduler becomes disconnected from the master, e.g.
        the master fails and another is taking over.

        See documentation for :meth:`mesos_api.mesos.Scheduler.disconnected`.
        '''

        if self.debug:
            connect_remote_debug()

        if self.master_hostname:
            logger.error('Scale scheduler disconnected from the Mesos master at %s:%i',
                         self.master_hostname, self.master_port)
        else:
            logger.error('Scale scheduler disconnected from the Mesos master')

    def resourceOffers(self, driver, offers):
        '''
        Invoked when resources have been offered to this framework. A single
        offer will only contain resources from a single slave.  Resources
        associated with an offer will not be re-offered to _this_ framework
        until either (a) this framework has rejected those resources (see
        SchedulerDriver.launchTasks) or (b) those resources have been
        rescinded (see Scheduler.offerRescinded).  Note that resources may be
        concurrently offered to more than one framework at a time (depending
        on the allocator being used).  In that case, the first framework to
        launch tasks using those resources will be able to use them while the
        other frameworks will have those resources rescinded (or if a
        framework has already launched tasks with those resources then those
        tasks will fail with a TASK_LOST status and a message saying as much).

        See documentation for :meth:`mesos_api.mesos.Scheduler.resourceOffers`.
        '''

        start_time = now()

        if self.debug:
            connect_remote_debug()

        # Compile a list of all of the offers and register nodes
        scale_offers = self._create_scale_offers(driver, offers)

        try:
            for scale_offer in scale_offers:
                logger.debug('Offer of %f CPUs, %f MiB memory, and %f MiB disk space from %s', scale_offer.cpus,
                             scale_offer.mem, scale_offer.disk, scale_offer.hostname)

            # Schedule any needed tasks for Scale jobs that are currently running even if the scheduler or individual nodes
            # are paused
            for scale_offer in scale_offers:
                slave_id = scale_offer.slave_id

                try:
                    Node.objects.update_last_offer(slave_id)
                except:
                    logger.exception('Error updating node last offer for slave_id %s', slave_id)

                with self.current_jobs_lock:
                    current_job_exes = self.current_jobs[slave_id]

                    for scale_job_exe in current_job_exes:
                        # Get updated remaining resources from offer
                        cpus = scale_offer.cpus
                        mem = scale_offer.mem
                        disk = scale_offer.disk
                        if scale_job_exe.is_next_task_ready(cpus, mem, disk):
                            try:
                                # We need to have the current_jobs lock when we do this
                                # and be using the real scale_job_exe not a copy
                                task = scale_job_exe.start_next_task()
                                cpus, mem, disk = scale_job_exe.get_current_task_resources()
                                scale_offer.add_task(task, cpus, mem, disk)
                            except:
                                logger.exception('Error trying to create Mesos task for job execution: %s',
                                                 scale_job_exe.job_exe_id)

            # Schedule jobs off of the queue. If the scheduler is paused, don't add new jobs
            #TODO: discuss into first() instead
            if models.Scheduler.objects.is_master_active():
                for scale_offer in scale_offers:
                    if scale_offer.can_run_new_jobs:
                        try:
                            scheduled_job_exes = Queue.objects.schedule_jobs_on_node(scale_offer.cpus, scale_offer.mem,
                                                                                     scale_offer.disk, scale_offer.node)
                            for job_exe in scheduled_job_exes:
                                scale_job_exe = ScaleJobExecution(job_exe, job_exe.cpus_scheduled, job_exe.mem_scheduled,
                                                                  job_exe.disk_in_scheduled, job_exe.disk_out_scheduled,
                                                                  job_exe.disk_total_scheduled)
                                task = scale_job_exe.start_next_task()
                                cpus, mem, disk = scale_job_exe.get_current_task_resources()
                                self._add_job_exe(scale_offer.slave_id, scale_job_exe)
                                scale_offer.add_task(task, cpus, mem, disk)
                        except:
                            logger.exception('Error trying to schedule a job off of the queue')

            # Tell Mesos to launch tasks!
            while len(scale_offers) > 0:
                scale_offer = scale_offers.pop(0)
                num_tasks = len(scale_offer.tasks)
                if num_tasks > 0:
                    logger.info('Scheduling %i task(s) on node: %s', num_tasks, scale_offer.hostname)
                else:
                    logger.debug('No tasks to schedule on node: %s', scale_offer.hostname)

                driver.launchTasks(scale_offer.offer_id, scale_offer.tasks)
        except:  # we must accept or decline all offers so there's a catch all here to ensure this happens
            for scale_offer in scale_offers:
                driver.launchTasks(scale_offer.offer_id, [])

        end_time = now()
        logger.debug('Time for resourceOffers: %s', str(end_time - start_time))

    def offerRescinded(self, driver, offerId):
        '''
        Invoked when an offer is no longer valid (e.g., the slave was lost or
        another framework used resources in the offer.) If for whatever reason
        an offer is never rescinded (e.g., dropped message, failing over
        framework, etc.), a framwork that attempts to launch tasks using an
        invalid offer will receive TASK_LOST status updats for those tasks.

        See documentation for :meth:`mesos_api.mesos.Scheduler.offerRescinded`.
        '''

        if self.debug:
            connect_remote_debug()

        logger.info('Offer rescinded: %s', offerId.value)

    def statusUpdate(self, driver, status):
        '''
        Invoked when the status of a task has changed (e.g., a slave is lost
        and so the task is lost, a task finishes and an executor sends a
        status update saying so, etc.) Note that returning from this callback
        acknowledges receipt of this status update.  If for whatever reason
        the scheduler aborts during this callback (or the process exits)
        another status update will be delivered.  Note, however, that this is
        currently not true if the slave sending the status update is lost or
        fails during that time.

        See documentation for :meth:`mesos_api.mesos.Scheduler.statusUpdate`.
        '''

        start_time = now()

        if self.debug:
            connect_remote_debug()

        status_str = utils.status_to_string(status.state)
        task_id = status.task_id.value
        job_exe_id = ScaleJobExecution.get_job_exe_id(task_id)
        logger.info('Status update for task %s: %s', task_id, status_str)

        # Got a status update, so remove task from reconciliation set
        try:
            self.recon_lock.acquire()
            if task_id in self.recon_set:
                self.recon_set.remove(task_id)
        finally:
            self.recon_lock.release()

        try:
            scale_job_exe = self._get_job_exe(job_exe_id)
            if not scale_job_exe:
                # Scheduler doesn't have any knowledge of this job execution
                error = get_scheduler_error()
                Queue.objects.handle_job_failure(job_exe_id, now(), error)
                return

            if status.state == mesos_pb2.TASK_RUNNING:
                scale_job_exe.task_running(task_id, status)
            elif status.state == mesos_pb2.TASK_FINISHED:
                scale_job_exe.task_completed(task_id, status)
            elif status.state in [mesos_pb2.TASK_LOST, mesos_pb2.TASK_ERROR,
                                  mesos_pb2.TASK_FAILED, mesos_pb2.TASK_KILLED]:
                # The task had an error so job execution is failed
                scale_job_exe.task_failed(task_id, status)
            if scale_job_exe.is_finished():
                # No more tasks so job execution is completed
                self._delete_job_exe(scale_job_exe)
        except:
            logger.exception('Error handling status update for job execution: %s', job_exe_id)
            # Error handling status update, add task so it can be reconciled
            try:
                self.recon_lock.acquire()
                self.recon_set.add(task_id)
            finally:
                self.recon_lock.release()

        end_time = now()
        logger.debug('Time for statusUpdate: %s', str(end_time - start_time))

    def frameworkMessage(self, driver, executorId, slaveId, message):
        '''
        Invoked when an executor sends a message. These messages are best
        effort; do not expect a framework message to be retransmitted in any
        reliable fashion.

        See documentation for :meth:`mesos_api.mesos.Scheduler.frameworkMessage`.
        '''

        if self.debug:
            connect_remote_debug()

        slave_id = slaveId.value
        node = None
        if slave_id in self.node_ids:
            node = Node.objects.get(id=self.node_ids[slave_id])
        else:
            try:
                node = Node.objects.get(slave_id=slave_id)
            except:
                logger.exception('Error retrieving node: %s', slave_id)

        if node:
            logger.info('Message from %s on host %s: %s', executorId, node.hostname, message)
        else:
            logger.info('Message from %s on slave %s: %s', executorId, slave_id, message)

    def slaveLost(self, driver, slaveId):
        '''
        Invoked when a slave has been determined unreachable (e.g., machine
        failure, network partition.) Most frameworks will need to reschedule
        any tasks launched on this slave on a new slave.

        See documentation for :meth:`mesos_api.mesos.Scheduler.slaveLost`.
        '''

        if self.debug:
            connect_remote_debug()

        slave_id = slaveId.value
        node = None
        if slave_id in self.node_ids:
            node = Node.objects.get(id=self.node_ids[slave_id])
        else:
            try:
                node = Node.objects.get(slave_id=slave_id)
            except:
                logger.exception('Error retrieving node: %s', slave_id)

        if node:
            logger.error('Node lost on host: %s', node.hostname)
        else:
            logger.error('Node lost on slave: %s', slave_id)

        # Fail all jobs that were scheduled on this node
        with self.current_jobs_lock:
            # The slave id may not have any current jobs,
            # so it may not be in the 'self.current_jobs' dict
            if slave_id not in self.current_jobs:
                return
            slave_job_exes = copy.deepcopy(self.current_jobs[slave_id])

        for scale_job_exe in slave_job_exes:
            try:
                error = get_node_lost_error()
                Queue.objects.handle_job_failure(scale_job_exe.job_exe_id, now(), error)
                self._delete_job_exe(scale_job_exe)
            except:
                logger.exception('Error setting job execution to FAILED: %s', scale_job_exe.job_exe_id)
                # Error failing job, add task so it can be reconciled
                task_id = scale_job_exe.current_task()
                if task_id:
                    try:
                        self.recon_lock.acquire()
                        self.recon_set.add(task_id)
                    finally:
                        self.recon_lock.release()

        # Remove references to lost node so it can be registered again
        del self.node_ids[slave_id]
        with self.current_jobs_lock:
            del self.current_jobs[slave_id]

    def executorLost(self, driver, executorId, slaveId, status):
        '''
        Invoked when an executor has exited/terminated. Note that any tasks
        running will have TASK_LOST status updates automatically generated.

        See documentation for :meth:`mesos_api.mesos.Scheduler.executorLost`.
        '''

        if self.debug:
            connect_remote_debug()

        slave_id = slaveId.value
        node = None
        if slave_id in self.node_ids:
            node = Node.objects.get(id=self.node_ids[slave_id])
        else:
            try:
                node = Node.objects.get(slave_id=slave_id)
            except Exception:
                logger.exception('Error retrieving node: %s', slave_id)

        if node:
            logger.error('Executor %s lost on host: %s', executorId.value, node.hostname)
        else:
            logger.error('Executor %s lost on slave: %s', executorId.value, slave_id)

    def error(self, driver, message):
        '''
        Invoked when there is an unrecoverable error in the scheduler or
        scheduler driver.  The driver will be aborted BEFORE invoking this
        callback.

        See documentation for :meth:`mesos_api.mesos.Scheduler.error`.
        '''

        if self.debug:
            connect_remote_debug()

        logger.error('Unrecoverable error: %s', message)

    def shutdown(self):
        '''Performs any clean up required by this scheduler implementation.

        Currently this method just notifies any background threads to break out of their work loops.
        '''
        logger.info('Scheduler shutdown invoked, flagging background threads to stop.')
        self.recon_running = False
        self.sync_database_running = False

    def _add_job_exe(self, slave_id, scale_job_exe):
        '''Adds the given Scale job execution to the list of current job executions

        :param slave_id: The slave ID
        :type slave_id: str
        :param scale_job_exe: The Scale job execution
        :type scale_job_exe: :class:`scheduler.job_exe.ScaleJobExecution`
        '''

        with self.current_jobs_lock:
            if slave_id in self.current_jobs:
                job_exe_list = self.current_jobs[slave_id]
            else:
                job_exe_list = []
                self.current_jobs[slave_id] = job_exe_list
            job_exe_list.append(scale_job_exe)

    def _create_scale_offers(self, driver, offers):
        '''Creates a list of Scale offers from the given Mesos offers

        :param driver: The scheduler driver
        :type driver: :class:`mesos.interface.SchedulerDriver`
        :param offers: The Mesos offers
        :type offers: list
        :returns: The list of Scale offers
        :rtype: list
        '''

        scale_offers = []
        for offer in offers:
            slave_id = offer.slave_id.value

            # Register node if scheduler doesn't have it in memory
            if not slave_id in self.node_ids:
                # Register node
                slave_info = None
                try:
                    slave_info = api.get_slave(self.master_hostname, self.master_port, slave_id)
                    node = Node.objects.register_node(slave_info.hostname, slave_info.port, slave_id)
                    with self.current_jobs_lock:
                        self.current_jobs[slave_id] = []
                    self.node_ids[slave_id] = node.id
                except:
                    logger.exception('Error registering node at %s, rejecting offer',
                                     slave_info.hostname if slave_info else slave_id)
                    # Decline offers where node registration failed
                    driver.launchTasks(offer.id, [])
                    continue
            else:
                node = Node.objects.get(id=self.node_ids[slave_id])

            scale_offers.append(ScaleOffer(offer, node))

        return scale_offers

    def _delete_job_exe(self, scale_job_exe):
        '''Deletes the given Scale job execution from the list of current job executions

        :param scale_job_exe: The Scale job execution
        :type scale_job_exe: :class:`scheduler.job_exe.ScaleJobExecution`
        '''

        with self.current_jobs_lock:
            for slave_id in self.current_jobs:
                job_exe_list = self.current_jobs[slave_id]
                if scale_job_exe in job_exe_list:
                    job_exe_list.remove(scale_job_exe)
                    break

    def _get_job_exe(self, job_exe_id):
        '''Retrieves a Scale job execution from the list of current job executions

        :param job_exe_id: The job execution ID
        :type job_exe_id: int
        :returns: The Scale job execution, possibly None
        :rtype: :class:`scheduler.job_exe.ScaleJobExecution`
        '''

        with self.current_jobs_lock:
            for slave_id in self.current_jobs:
                job_exe_list = self.current_jobs[slave_id]
                for scale_job_exe in job_exe_list:
                    if scale_job_exe.job_exe_id == job_exe_id:
                        return scale_job_exe

        return None

    def _get_job_exes(self):
        '''Retrieves a list of all currently running Scale job executions

        :returns: The list of Scale job executions
        :rtype: [:class:`scheduler.job_exe.ScaleJobExecution`]
        '''

        job_exes = []
        with self.current_jobs_lock:
            for slave_id in self.current_jobs:
                job_exe_list = self.current_jobs[slave_id]
                for scale_job_exe in job_exe_list:
                    job_exes.append(scale_job_exe)

        return job_exes

    def _get_jobs_to_kill(self):
        '''gets jobs that are past their timeout that are not already timed_out
        :returns: A list of Scale job executions that have timed out and should be killed'''
        jobs_past_timeout = []
        with self.current_jobs_lock:
            for job_exe_list in self.current_jobs.values():
                for scale_job_exe in job_exe_list:
                    if (scale_job_exe.timeout is not None) and (scale_job_exe.timeout < now()):
                        jobs_past_timeout.append(scale_job_exe)
        return jobs_past_timeout

    def _perform_reconciliation(self):
        '''Performs reconciliation with Mesos by querying for the status of all
        tasks in the reconciliation set
        '''
        throttle = 60

        logger.info('Scheduler reconciliation background thread started.')
        while self.recon_running:
            try:
                secs_passed = 0
                started = now()

                # Get list of task IDs to reconcile
                try:
                    recon_list = []
                    self.recon_lock.acquire()
                    for task_id in self.recon_set:
                        recon_list.append(task_id)
                finally:
                    self.recon_lock.release()

                if not recon_list:
                    continue

                logger.info('Performing reconciliation for %i task(s)', len(recon_list))
                tasks = []
                for task_id in recon_list:
                    task = mesos_pb2.TaskStatus()
                    task.task_id.value = task_id
                    task.state = mesos_pb2.TASK_LOST
                    # TODO: adding task.slave_id would be useful if possible
                    tasks.append(task)
                self.driver.reconcileTasks(tasks)

                ended = now()
                secs_passed = (ended - started).total_seconds()
            except:
                logger.exception('Scheduler reconciliation thread encountered error')
            finally:
                # TODO: Mesos docs recommends truncated exponential backoff
                # If time takes less than a minute, throttle
                if secs_passed < throttle:
                    # Delay until full throttle time reached
                    delay = math.ceil(throttle - secs_passed)
                    time.sleep(delay)
        logger.info('Scheduler reconciliation background thread stopped.')

    def _reconcile_running_jobs(self):
        '''Looks up all currently running jobs and adds them to the set so that they can be reconciled
        '''

        # List of task IDs to reconcile
        task_id_list = []

        # Query for jobs that are in RUNNING status
        job_exes = JobExecution.objects.get_running_job_exes()

        # Look through scheduler data and find current task ID for each
        # RUNNING job
        for job_exe in job_exes:
            scale_job_exe = self._get_job_exe(job_exe.id)
            if scale_job_exe:
                task_id = scale_job_exe.current_task()
                if task_id:
                    task_id_list.append(task_id)
            else:
                # Fail any jobs that the scheduler doesn't know about
                error = get_scheduler_error()
                Queue.objects.handle_job_failure(job_exe.id, now(), error)

        # Add currently running task IDs to set to be reconciled
        try:
            self.recon_lock.acquire()
            for task_id in task_id_list:
                self.recon_set.add(task_id)
        finally:
            self.recon_lock.release()

    def _sync_with_database_thread(self):
        '''This method is a background thread that polls the database to check for updates to the job executions that
        are currently running in the scheduler. This method kills off job executions that have been canceled. It also
        kills and fails job executions that have timed out.
        '''
        throttle = 10

        logger.info('Scheduler database sync background thread started')

        while self.sync_database_running:
            secs_passed = 0
            started = now()

            job_exes = self._get_job_exes()
            job_exe_ids = []
            for job_exe in job_exes:
                job_exe_ids.append(job_exe.job_exe_id)

            try:
                right_now = now()
                for job_exe_model in JobExecution.objects.filter(id__in=job_exe_ids):
                    try:
                        for job_exe in job_exes:
                            if job_exe.job_exe_id == job_exe_model.id:
                                this_job_exe = job_exe
                                break
                        kill_task = False
                        delete_job_exe = False
                        if job_exe_model.status == 'CANCELED':
                            kill_task = True
                            delete_job_exe = True
                        elif job_exe_model.is_timed_out(right_now):
                            kill_task = True
                            delete_job_exe = True
                            error = get_timeout_error()
                            Queue.objects.handle_job_failure(job_exe_model.id, right_now, error)
                        if kill_task:
                            task_to_kill_id = this_job_exe.current_task()
                            if task_to_kill_id:
                                pb_task_to_kill = mesos_pb2.TaskID()
                                pb_task_to_kill.value = task_to_kill_id
                                logger.info('About to kill task: %s', task_to_kill_id)
                                self.driver.killTask(pb_task_to_kill)
                        if delete_job_exe:
                            self._delete_job_exe(this_job_exe)
                    except Exception:
                        logger.exception('Error syncing scheduler with database for job_exe %s', job_exe_model.id)
            except Exception:
                logger.exception('Error syncing scheduler with database')

            ended = now()
            secs_passed = (ended - started).total_seconds()
            if secs_passed < throttle:
                # Delay until full throttle time reached
                delay = math.ceil(throttle - secs_passed)
                time.sleep(delay)

        logger.info('Scheduler database sync background thread stopped')
