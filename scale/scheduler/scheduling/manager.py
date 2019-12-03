"""Defines the class that manages all scheduling"""
from __future__ import absolute_import
from __future__ import unicode_literals

import datetime
import logging

from django.db import transaction
from django.db.utils import DatabaseError
from django.utils.timezone import now

from job.configuration.data.exceptions import InvalidConfiguration
from job.execution.configuration.configurators import ScheduledExecutionConfigurator
from job.execution.job_exe import RunningJobExecution
from job.execution.manager import job_exe_mgr
from job.messages.running_jobs import create_running_job_messages
from job.models import Job, JobExecution, JobExecutionEnd
from job.tasks.manager import task_mgr
from mesos_api.tasks import create_mesos_task
from node.resources.node_resources import NodeResources
from queue.job_exe import QueuedJobExecution
from queue.models import Queue
from scheduler.cleanup.manager import cleanup_mgr
from scheduler.manager import scheduler_mgr, SchedulerWarning
from scheduler.node.manager import node_mgr
from scheduler.resources.agent import ResourceSet
from scheduler.resources.manager import resource_mgr
from scheduler.scheduling.scheduling_node import SchedulingNode
from scheduler.sync.job_type_manager import job_type_mgr
from scheduler.sync.workspace_manager import workspace_mgr
from scheduler.tasks.manager import system_task_mgr
from util.retry import retry_database_query

# Warning threshold for queue processing duration
PROCESS_QUEUE_WARN_THRESHOLD = datetime.timedelta(milliseconds=300)
# Maximum number of jobs to grab off of the queue at one time
QUEUE_LIMIT = 500
# Warning threshold for scheduling query duration
SCHEDULE_QUERY_WARN_THRESHOLD = datetime.timedelta(milliseconds=300)
# Warning threshold for task launch duration
LAUNCH_TASK_WARN_THRESHOLD = datetime.timedelta(milliseconds=300)

# It is considered a resource shortage if a task waits this many generations without being scheduled
TASK_SHORTAGE_WAIT_COUNT = 10

logger = logging.getLogger(__name__)


# Warnings
INVALID_RESOURCES = SchedulerWarning(name='INVALID_RESOURCES', title='Invalid Resources for %s',
                                     description='Cluster does not have one or more of the following resources: %s.')
INSUFFICIENT_RESOURCES = SchedulerWarning(name='INSUFFICIENT_RESOURCES', title='Insufficient Resources for %s',
                                     description='No node has enough of this resource for the job type: %s.')
WAITING_SYSTEM_TASKS = SchedulerWarning(name='WAITING_SYSTEM_TASKS', title='Waiting System Tasks',
                                     description='No new jobs scheduled due to waiting system tasks')
UNKNOWN_JOB_TYPE = SchedulerWarning(name='UNKNOWN_JOB_TYPE', title='Unknown Job Type',
                                     description='A job is queued with a job type %d that is not in the data base')

class SchedulingManager(object):
    """This class manages all scheduling. This class is NOT thread-safe and should only be used within the scheduling
    thread.
    """

    def __init__(self):
        """Constructor
        """

        self._waiting_tasks = {}  # {Task ID: int}

    def perform_scheduling(self, client, when):
        """Organizes and analyzes the cluster resources, schedules new job executions, and launches tasks

        :param client: The Mesos scheduler client
        :type client: :class:`mesoshttp.client.MesosClient`
        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: The number of tasks that were scheduled
        :rtype: int
        """
        # Get framework ID first to make sure it doesn't change throughout scheduling process
        framework_id = scheduler_mgr.framework_id
        if not framework_id or not client or not client.get_driver():
            # Don't schedule anything until the scheduler has connected to Mesos
            logger.warning('Scheduler not connected to Mesos. Scheduling delayed until connection established.')
            return 0

        job_types = job_type_mgr.get_job_types()
        job_type_resources = job_type_mgr.get_job_type_resources()
        tasks = task_mgr.get_all_tasks()
        running_job_exes = job_exe_mgr.get_running_job_exes()
        workspaces = workspace_mgr.get_workspaces()
        nodes = self._prepare_nodes(tasks, running_job_exes, when)
        fulfilled_nodes = self._schedule_waiting_tasks(nodes, running_job_exes, when)

        sys_tasks_scheduled = self._schedule_system_tasks(fulfilled_nodes, job_type_resources, when)

        job_exe_count = 0
        if sys_tasks_scheduled:
            # Only schedule new job executions if all needed system tasks have been scheduled
            job_type_limits = self._calculate_job_type_limits(job_types, running_job_exes)
            job_exe_count = self._schedule_new_job_exes(framework_id, fulfilled_nodes, job_types, job_type_limits,
                                                        job_type_resources, workspaces)
        else:
            logger.warning('No new jobs scheduled due to waiting system tasks')
            scheduler_mgr.warning_active(WAITING_SYSTEM_TASKS)

        if framework_id != scheduler_mgr.framework_id:
            logger.warning('Scheduler framework ID changed, skipping task launch')
            return 0

        self._allocate_offers(nodes)
        declined = resource_mgr.decline_offers()
        self._decline_offers(declined)
        task_count, offer_count = self._launch_tasks(client, nodes)
        scheduler_mgr.add_scheduling_counts(job_exe_count, task_count, offer_count)
        return task_count

    def _allocate_offers(self, nodes):
        """Allocates resource offers to the node

        :param nodes: The dict of all scheduling nodes stored by node ID
        :type nodes: dict
        """

        allocated_resources = {}
        for node in nodes.values():
            allocated_resources[node.agent_id] = node.allocated_resources

        resources_offers = resource_mgr.allocate_offers(allocated_resources, now())  # Use most recent time

        for node in nodes.values():
            offers = []
            if node.agent_id in resources_offers:
                offers = resources_offers[node.agent_id]
            node.add_allocated_offers(offers)

    def _calculate_job_type_limits(self, job_types, running_job_exes):
        """Calculates and returns the available job type limits

        :param job_types: The dict of job type models stored by job type ID
        :type job_types: dict
        :param running_job_exes: The currently running job executions
        :type running_job_exes: list
        :returns: A dict where job type ID maps to the number of jobs of that type that can be scheduled. Missing job
            type IDs have no limit. Counts may be negative if the job type is scheduled above the limit.
        :rtype: dict
        """

        job_type_limits = {}
        for job_type in job_types.values():
            if job_type.max_scheduled:
                job_type_limits[job_type.id] = job_type.max_scheduled
        for running_job_exe in running_job_exes:
            if running_job_exe.job_type_id in job_type_limits:
                job_type_limits[running_job_exe.job_type_id] -= 1

        return job_type_limits

    def _calculate_job_types_to_ignore(self, job_types, job_type_limits):
        """Calculates and returns the set of ID for job types to ignore on the queue

        :param job_types: The dict of job type models stored by job type ID
        :type job_types: dict
        :param job_type_limits: The dict of job type IDs mapping to job type limits
        :type job_type_limits: dict
        :returns: A set of the job type IDs to ignore
        :rtype: set
        """

        ignore_job_type_ids = set()

        # Ignore paused job types
        for job_type in job_types.values():
            if job_type.is_paused:
                ignore_job_type_ids.add(job_type.id)

        # Ignore job types that have reached their max scheduling limits
        for job_type_id in job_type_limits:
            if job_type_limits[job_type_id] < 1:
                ignore_job_type_ids.add(job_type_id)

        return ignore_job_type_ids

    def _decline_offers(self, offers):
        """Declines offers that have not been allocated

        :param offers: The Mesos offers
        :type offers: :class:`mesoshttp.offers.Offer`
        """

        for offer in offers:
            if offer.mesos_offer:
                offer.mesos_offer.decline()
            else:
                logger.debug("Trying to decline offer without original mesos_offer object")
        
        logger.debug("Declined %d offers" % len(offers))

    def _launch_tasks(self, client, nodes):
        """Launches all of the tasks that have been scheduled on the given nodes

        :param client: The Mesos scheduler client
        :type client: :class:`mesoshttp.client.MesosClient`
        :param nodes: The dict of all scheduling nodes stored by node ID
        :type nodes: dict
        :returns: The number of tasks that were launched and the number of offers accepted
        :rtype: tuple
        """

        started = now()

        # Start and launch tasks in the task manager
        all_tasks = []
        for node in nodes.values():
            node.start_job_exe_tasks()
            all_tasks.extend(node.allocated_tasks)
        task_mgr.launch_tasks(all_tasks, started)

        # Launch tasks in Mesos
        node_count = 0
        total_node_count = 0
        total_offer_count = 0
        total_task_count = 0
        total_offer_resources = NodeResources()
        total_task_resources = NodeResources()
        for node in nodes.values():
            mesos_offers = []
            mesos_tasks = []
            offers = node.allocated_offers
            for offer in offers:
                total_offer_count += 1
                total_offer_resources.add(offer.resources)
                mesos_offers.append(offer.mesos_offer)
            tasks = node.allocated_tasks
            for task in tasks:
                total_task_resources.add(task.get_resources())
                mesos_tasks.append(create_mesos_task(task))
            task_count = len(tasks)
            total_task_count += task_count
            if task_count:
                node_count += 1
            if mesos_offers:
                total_node_count += 1
                try:
                    client.combine_offers(mesos_offers, mesos_tasks)
                except Exception:
                    logger.exception('Error occurred while launching tasks on node %s', node.hostname)

        duration = now() - started
        msg = 'Launching tasks took %.3f seconds'
        if duration > LAUNCH_TASK_WARN_THRESHOLD:
            logger.warning(msg, duration.total_seconds())
        else:
            logger.debug(msg, duration.total_seconds())

        declined_resources = NodeResources()
        declined_resources.add(total_offer_resources)
        declined_resources.subtract(total_task_resources)
        if total_offer_count:
            logger.info('Accepted %d offer(s) from %d node(s), launched %d task(s) with %s on %d node(s), declined %s',
                        total_offer_count, total_node_count, total_task_count, total_task_resources, node_count,
                        declined_resources)
        return total_task_count, total_offer_count

    def _prepare_nodes(self, tasks, running_job_exes, when):
        """Prepares the nodes to use for scheduling

        :param tasks: The current current running
        :type tasks: list
        :param running_job_exes: The currently running job executions
        :type running_job_exes: list
        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: The dict of scheduling nodes stored by node ID
        :rtype: dict
        """

        nodes = node_mgr.get_nodes()

        # Group tasks by agent ID
        tasks_by_agent_id = {}  # {Agent ID: List of tasks}
        for task in tasks:
            if task.agent_id not in tasks_by_agent_id:
                tasks_by_agent_id[task.agent_id] = [task]
            else:
                tasks_by_agent_id[task.agent_id].append(task)

        # Group job executions by node ID
        running_exes_by_node_id = {}  # {Node ID: List of running job exes}
        for running_job_exe in running_job_exes:
            if running_job_exe.node_id not in running_exes_by_node_id:
                running_exes_by_node_id[running_job_exe.node_id] = [running_job_exe]
            else:
                running_exes_by_node_id[running_job_exe.node_id].append(running_job_exe)

        agent_resources = resource_mgr.refresh_agent_resources(tasks, when)

        scheduling_nodes = {}  # {Node ID: SchedulingNode}
        for node in nodes:
            agent_id = node.agent_id   # Grab agent ID once since it could change while we are scheduling

            if agent_id in tasks_by_agent_id:
                node_tasks = tasks_by_agent_id[agent_id]
            else:
                node_tasks = []
            if node.id in running_exes_by_node_id:
                node_exes = running_exes_by_node_id[node.id]
            else:
                node_exes = []
            if agent_id in agent_resources:
                resource_set = agent_resources[agent_id]
            else:
                resource_set = ResourceSet()

            scheduling_node = SchedulingNode(agent_id, node, node_tasks, node_exes, resource_set)
            scheduling_nodes[scheduling_node.node_id] = scheduling_node
        return scheduling_nodes

    def _process_queue(self, nodes, job_types, job_type_limits, job_type_resources, workspaces):
        """Retrieves the top of the queue and schedules new job executions on available nodes as resources and limits
        allow

        :param nodes: The dict of scheduling nodes stored by node ID for all nodes ready to accept new job executions
        :type nodes: dict
        :param job_types: The dict of job type models stored by job type ID
        :type job_types: dict
        :param job_type_limits: The dict of job type IDs mapping to job type limits
        :type job_type_limits: dict
        :param job_type_resources: The list of all of the job type resource requirements
        :type job_type_resources: list
        :param workspaces: A dict of all workspaces stored by name
        :type workspaces: dict
        :returns: The list of queued job executions that were scheduled
        :rtype: list
        """

        scheduled_job_executions = []
        ignore_job_type_ids = self._calculate_job_types_to_ignore(job_types, job_type_limits)
        started = now()

        max_cluster_resources = resource_mgr.get_max_available_resources()
        for queue in Queue.objects.get_queue(scheduler_mgr.config.queue_mode, ignore_job_type_ids).iterator():
            job_exe = QueuedJobExecution(queue)

            # Canceled job executions get processed as scheduled executions
            if job_exe.is_canceled:
                scheduled_job_executions.append(job_exe)
                continue

            # If there are no longer any available nodes, break
            if not nodes:
                logger.warning('There are no nodes available. Waiting to schedule until there are free resources...')
                break

            jt = job_type_mgr.get_job_type(queue.job_type.id)
            name = INVALID_RESOURCES.name + jt.name
            title = INVALID_RESOURCES.title % jt.name
            warning = SchedulerWarning(name=name, title=title, description=None)
            if jt.unmet_resources and scheduler_mgr.is_warning_active(warning):
                # previously checked this job type and found we lacked resources; wait until warning is inactive to check again
                continue

            invalid_resources = []
            insufficient_resources = []
            # get resource names offered and compare to job type resources
            for resource in job_exe.required_resources.resources:
                # skip sharedmem
                if resource.name.lower() == 'sharedmem':
                    logger.warning('Job type %s could not be scheduled due to required sharedmem resource', jt.name)
                    continue
                if resource.name not in max_cluster_resources._resources:
                    # resource does not exist in cluster
                    invalid_resources.append(resource.name)
                elif resource.value > max_cluster_resources._resources[resource.name].value:
                    # resource exceeds the max available from any node
                    insufficient_resources.append(resource.name)

            if invalid_resources:
                description = INVALID_RESOURCES.description % invalid_resources
                scheduler_mgr.warning_active(warning, description)

            if insufficient_resources:
                description = INSUFFICIENT_RESOURCES.description % insufficient_resources
                scheduler_mgr.warning_active(warning, description)

            if invalid_resources or insufficient_resources:
                invalid_resources.extend(insufficient_resources)
                jt.unmet_resources = ','.join(invalid_resources)
                jt.save(update_fields=["unmet_resources"])
                continue
            else:
                # reset unmet_resources flag
                jt.unmet_resources = None
                scheduler_mgr.warning_inactive(warning)
                jt.save(update_fields=["unmet_resources"])

            # Make sure execution's job type and workspaces have been synced to the scheduler
            job_type_id = queue.job_type_id
            if job_type_id not in job_types:
                scheduler_mgr.warning_active(UNKNOWN_JOB_TYPE, description=UNKNOWN_JOB_TYPE.description % job_type_id)
                continue

            workspace_names = job_exe.configuration.get_input_workspace_names()
            workspace_names.extend(job_exe.configuration.get_output_workspace_names())

            missing_workspace = False
            for name in workspace_names:
                missing_workspace = missing_workspace or name not in workspaces
            if missing_workspace:
                logger.warning('Job type %s could not be scheduled due to missing workspace', jt.name)
                continue

            # Check limit for this execution's job type
            if job_type_id in job_type_limits and job_type_limits[job_type_id] < 1:
                logger.warning('Job type %s could not be scheduled due to type scheduling limit reached ', jt.name)
                continue

            # Try to schedule job execution and adjust job type limit if needed
            if self._schedule_new_job_exe(job_exe, nodes, job_type_resources):
                scheduled_job_executions.append(job_exe)
                if job_type_id in job_type_limits:
                    job_type_limits[job_type_id] -= 1

            if len(scheduled_job_executions) >= QUEUE_LIMIT:
                logger.info('Schedule queue limit of %d reached; no more room for executions' % QUEUE_LIMIT)
                break

        duration = now() - started
        msg = 'Processing queue took %.3f seconds'
        if duration > PROCESS_QUEUE_WARN_THRESHOLD:
            logger.warning(msg, duration.total_seconds())
        else:
            logger.debug(msg, duration.total_seconds())

        return scheduled_job_executions

    @retry_database_query(max_tries=5, base_ms_delay=1000, max_ms_delay=5000)
    def _process_scheduled_job_executions(self, framework_id, queued_job_executions, job_types, workspaces):
        """Processes the given queued job executions that have been scheduled and returns the new running job
        executions. All database updates occur in an atomic transaction.

        :param framework_id: The scheduling framework ID
        :type framework_id: string
        :param queued_job_executions: A list of queued job executions that have been scheduled
        :type queued_job_executions: list
        :param job_types: A dict of all job types stored by ID
        :type job_types: dict
        :param workspaces: A dict of all workspaces stored by name
        :type workspaces: dict
        :returns: The running job executions stored in lists by node ID
        :rtype: dict
        """

        started = now()
        running_job_exes = {}
        configurator = ScheduledExecutionConfigurator(workspaces)

        with transaction.atomic():
            # Bulk create the job execution models
            job_exe_models = []
            scheduled_models = {}  # {queue ID: (job_exe model, config)}
            canceled_models = {}  # {queue ID: job_exe model}
            for queued_job_exe in queued_job_executions:
                job_exe_model = queued_job_exe.create_job_exe_model(framework_id, started)
                job_exe_models.append(job_exe_model)
                if queued_job_exe.is_canceled:
                    canceled_models[queued_job_exe.id] = job_exe_model
                else:
                    job_type = job_types[job_exe_model.job_type_id]
                    # The configuration stored in the job_exe model has been censored so it is safe to save in database
                    # The returned configuration may contain secrets and should be passed to running job_exe for use
                    config = configurator.configure_scheduled_job(job_exe_model, job_type, queued_job_exe.interface, scheduler_mgr.config.system_logging_level)
                    scheduled_models[queued_job_exe.id] = (job_exe_model, config)
            JobExecution.objects.bulk_create(job_exe_models)

            # Create running and canceled job executions
            queue_ids = []
            canceled_job_exe_end_models = []
            for queued_job_exe in queued_job_executions:
                queue_ids.append(queued_job_exe.id)
                if queued_job_exe.is_canceled:
                    job_exe_model = canceled_models[queued_job_exe.id]
                    canceled_job_exe_end_models.append(job_exe_model.create_canceled_job_exe_end_model(started))
                else:
                    agent_id = queued_job_exe.scheduled_agent_id
                    job_exe_model = scheduled_models[queued_job_exe.id][0]
                    job_type = job_types[job_exe_model.job_type_id]
                    config = scheduled_models[queued_job_exe.id][1]  # May contain secrets!
                    priority = queued_job_exe.priority
                    running_job_exe = RunningJobExecution(agent_id, job_exe_model, job_type, config, priority)
                    if running_job_exe.node_id in running_job_exes:
                        running_job_exes[running_job_exe.node_id].append(running_job_exe)
                    else:
                        running_job_exes[running_job_exe.node_id] = [running_job_exe]

            # Add canceled job execution end models to manager to be sent to messaging backend
            if canceled_job_exe_end_models:
                job_exe_mgr.add_canceled_job_exes(canceled_job_exe_end_models)

            # Delete queue models
            Queue.objects.filter(id__in=queue_ids).delete()

        duration = now() - started
        msg = 'Queries to process scheduled jobs took %.3f seconds'
        if duration > SCHEDULE_QUERY_WARN_THRESHOLD:
            logger.warning(msg, duration.total_seconds())
        else:
            logger.debug(msg, duration.total_seconds())

        return running_job_exes

    def _schedule_new_job_exe(self, job_exe, nodes, job_type_resources):
        """Schedules the given job execution on the queue on one of the available nodes, if possible

        :param job_exe: The job execution to schedule
        :type job_exe: :class:`queue.job_exe.QueuedJobExecution`
        :param nodes: The dict of available scheduling nodes stored by node ID
        :type nodes: dict
        :param job_type_resources: The list of all of the job type resource requirements
        :type job_type_resources: list
        :returns: True if scheduled, False otherwise
        :rtype: bool
        """

        best_scheduling_node = None
        best_scheduling_score = None
        best_reservation_node = None
        best_reservation_score = None

        for node in nodes.values():
            # Check node for scheduling this job execution
            score = node.score_job_exe_for_scheduling(job_exe, job_type_resources)
            if score is not None:
                # Job execution could be scheduled on this node, check its score
                if best_scheduling_node is None or score < best_scheduling_score:
                    # This is the best node for scheduling so far
                    best_scheduling_node = node
                    best_scheduling_score = score
                    best_reservation_node = None  # No need to reserve a node if we can schedule the job execution
                    best_reservation_score = None  # No need to reserve a node if we can schedule the job execution

            if best_scheduling_node is None:
                # No nodes yet to schedule this job execution on, check whether we should reserve this node
                score = node.score_job_exe_for_reservation(job_exe, job_type_resources)
                if score is not None:
                    # Job execution could reserve this node, check its score
                    if best_reservation_node is None or score < best_reservation_score:
                        # This is the best node to reserve so far
                        best_reservation_node = node
                        best_reservation_score = score

        # Schedule the job execution on the best node
        if best_scheduling_node:
            if best_scheduling_node.accept_new_job_exe(job_exe):
                return True

        # Could not schedule job execution, reserve a node to run this execution if possible
        if best_reservation_node:
            del nodes[best_reservation_node.node_id]

        return False

    def _schedule_new_job_exes(self, framework_id, nodes, job_types, job_type_limits, job_type_resources, workspaces):
        """Schedules new job executions from the queue and adds them to the appropriate node

        :param framework_id: The scheduling framework ID
        :type framework_id: string
        :param nodes: The dict of scheduling nodes stored by node ID where every node has fulfilled all waiting tasks
        :type nodes: dict
        :param job_types: The dict of job type models stored by job type ID
        :type job_types: dict
        :param job_type_limits: The dict of job type IDs mapping to job type limits
        :type job_type_limits: dict
        :param job_type_resources: The list of all of the job type resource requirements
        :type job_type_resources: list
        :param workspaces: A dict of all workspaces stored by name
        :type workspaces: dict
        :returns: The number of new job executions that were scheduled
        :rtype: int
        """

        # Can only use nodes that are ready for new job executions
        available_nodes = {}  # {Node ID: SchedulingNode}
        for node in nodes.values():
            if node.is_ready_for_new_job:
                available_nodes[node.node_id] = node

        try:
            scheduled_job_exes = self._process_queue(available_nodes, job_types, job_type_limits, job_type_resources,
                                                     workspaces)
            running_job_exes = self._process_scheduled_job_executions(framework_id, scheduled_job_exes, job_types,
                                                                      workspaces)
            all_running_job_exes = []
            for node_id in running_job_exes:
                all_running_job_exes.extend(running_job_exes[node_id])
            job_exe_mgr.schedule_job_exes(all_running_job_exes, create_running_job_messages(all_running_job_exes))
            node_ids = set()
            job_exe_count = 0
            scheduled_resources = NodeResources()
            for node_id in running_job_exes:
                if node_id in nodes:
                    nodes[node_id].add_scheduled_job_exes(running_job_exes[node_id])
                    for running_job_exe in running_job_exes[node_id]:
                        first_task = running_job_exe.next_task()
                        if first_task:
                            node_ids.add(node_id)
                            scheduled_resources.add(first_task.get_resources())
                            job_exe_count += 1
                else:
                    logger.error('Scheduled jobs on an unknown node')
            if job_exe_count:
                logger.info('Scheduled %d new job(s) with %s on %d node(s)', job_exe_count, scheduled_resources,
                            len(node_ids))
        except DatabaseError:
            logger.exception('Error occurred while scheduling new jobs from the queue')
            job_exe_count = 0
            for node in available_nodes.values():
                node.reset_new_job_exes()

        return job_exe_count

    def _schedule_system_tasks(self, nodes, job_type_resources, when):
        """Schedules all system tasks for which there are sufficient resources and indicates whether all system tasks
        were able to be scheduled

        :param nodes: The dict of scheduling nodes stored by node ID where every node has fulfilled all waiting tasks
        :type nodes: dict
        :param job_type_resources: The list of all of the job type resource requirements
        :type job_type_resources: list
        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: True if all system tasks were scheduled as needed, False otherwise
        :rtype: bool
        """

        node_ids = set()
        scheduled_tasks = 0
        scheduled_resources = NodeResources()
        waiting_tasks = 0
        waiting_resources = NodeResources()

        for task in system_task_mgr.get_tasks_to_schedule(when):
            task_scheduled = False
            best_scheduling_node = None
            best_scheduling_score = None
            for node in nodes.values():
                # Check node for scheduling this system task
                score = node.score_system_task_for_scheduling(task, job_type_resources)
                if score is not None:
                    # System task could be scheduled on this node, check its score
                    if best_scheduling_node is None or score < best_scheduling_score:
                        # This is the best node for scheduling so far
                        best_scheduling_node = node
                        best_scheduling_score = score

            # Schedule the system task on the best node
            if best_scheduling_node:
                if best_scheduling_node.accept_system_task(task):
                    task_scheduled = True
                    node_ids.add(best_scheduling_node.node_id)

            if task_scheduled:
                scheduled_tasks += 1
                scheduled_resources.add(task.get_resources())
            else:
                waiting_tasks += 1
                waiting_resources.add(task.get_resources())

        if scheduled_tasks:
            logger.info('Scheduled %d system task(s) with %s on %d node(s)', scheduled_tasks, scheduled_resources,
                        len(node_ids))
        if waiting_tasks:
            logger.warning('%d system task(s) with %s are waiting to be scheduled', waiting_tasks, waiting_resources)
        return waiting_tasks == 0

    def _schedule_waiting_tasks(self, nodes, running_job_exes, when):
        """Schedules all waiting tasks for which there are sufficient resources and updates the resource manager with
        any resource shortages. All scheduling nodes that have fulfilled all of their waiting tasks will be returned so
        new job executions can be added to them.

        :param nodes: The dict of scheduling nodes stored by node ID
        :type nodes: dict
        :param running_job_exes: The currently running job executions
        :type running_job_exes: list
        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: The dict of scheduling nodes stored by node ID that have no more waiting tasks
        :rtype: dict
        """

        fulfilled_nodes = {}  # {Node ID: SchedulingNode}
        waiting_tasks = []

        # Schedule waiting node tasks first
        for node in nodes.values():
            has_waiting_tasks = node.accept_node_tasks(when, waiting_tasks)
            if node.is_ready_for_next_job_task and not has_waiting_tasks:
                # A node can only be fulfilled if it is able to run waiting tasks and it has no more waiting tasks
                fulfilled_nodes[node.node_id] = node

        # Schedule job executions already on the node waiting for their next task
        node_lost_job_exes_ids = []
        for running_job_exe in running_job_exes:
            if running_job_exe.node_id not in nodes:  # Unknown/lost node
                node_lost_job_exes_ids.append(running_job_exe.id)
            else:
                node = nodes[running_job_exe.node_id]
                if not node.is_ready_for_next_job_task or node.agent_id != running_job_exe.agent_id:
                    # Node is deprecated, offline, or has switched agent IDs
                    node_lost_job_exes_ids.append(running_job_exe.id)
                elif running_job_exe.is_next_task_ready():
                    has_waiting_tasks = node.accept_job_exe_next_task(running_job_exe, waiting_tasks)
                    if has_waiting_tasks and node.node_id in fulfilled_nodes:
                        # Node has tasks waiting for resources
                        del fulfilled_nodes[node.node_id]
        # Handle any running job executions that have lost their node or become starved
        finished_job_exes = job_exe_mgr.check_for_starvation(when)
        if node_lost_job_exes_ids:
            finished_job_exes.extend(job_exe_mgr.lost_job_exes(node_lost_job_exes_ids, when))
        for finished_job_exe in finished_job_exes:
            cleanup_mgr.add_job_execution(finished_job_exe)

        # Update waiting task counts and calculate shortages
        agent_shortages = {}  # {Agent ID: NodeResources}
        new_waiting_tasks = {}  # {Task ID: int}
        for task in waiting_tasks:
            if task.id in self._waiting_tasks:
                count = self._waiting_tasks[task.id] + 1
            else:
                count = 1
            new_waiting_tasks[task.id] = count
            if count >= TASK_SHORTAGE_WAIT_COUNT:
                # This task has waited too long for resources, generate a shortage
                if task.agent_id in agent_shortages:
                    agent_shortages[task.agent_id].add(task.get_resources())
                else:
                    resources = NodeResources()
                    resources.add(task.get_resources())
                    agent_shortages[task.agent_id] = resources
        self._waiting_tasks = new_waiting_tasks
        resource_mgr.set_agent_shortages(agent_shortages)

        return fulfilled_nodes
