"""Defines the database model for a queue entry"""
from __future__ import unicode_literals

import abc
import logging

import django.utils.timezone as timezone
import django.contrib.postgres.fields
from django.db import models, transaction

from error.models import Error
from job.configuration.data.exceptions import InvalidData
from job.configuration.data.job_data import JobData
from job.configuration.json.execution.exe_config import ExecutionConfiguration
from job.execution.job_exe import RunningJobExecution
from job.models import Job, JobType
from job.models import JobExecution
from node.resources.json.resources import Resources
from recipe.models import Recipe
from trigger.models import TriggerEvent

logger = logging.getLogger(__name__)

QUEUE_ORDER_FIFO = 'FIFO'
QUEUE_ORDER_LIFO = 'LIFO'
DEFAULT_QUEUE_ORDER = QUEUE_ORDER_FIFO

# IMPORTANT NOTE: Locking order
# Always adhere to the following model order for obtaining row locks via select_for_update() in order to prevent
# deadlocks and ensure query efficiency
# When applying status updates to jobs: JobExecution, Queue, Job, Recipe
# When editing a job/recipe type: RecipeType, JobType, TriggerRule


class JobLoadGroup(object):
    """Represents a group of job load models.

    :keyword time: When the counts were actually measured.
    :type time: datetime.datetime
    :keyword pending_count: The number of jobs in pending status for the type.
    :type pending_count: int
    :keyword queued_count: The number of jobs in queued status for the type.
    :type queued_count: int
    :keyword running_count: The number of jobs in running status for the type.
    :type running_count: int
    """
    def __init__(self, time, pending_count=0, queued_count=0, running_count=0):
        self.time = time
        self.pending_count = pending_count
        self.queued_count = queued_count
        self.running_count = running_count


class JobLoadManager(models.Manager):
    """This class manages the JobLoad model."""

    @transaction.atomic
    def calculate(self):
        """Calculates and saves new job load models grouped by job type based on a current jobs snapshot."""

        # Get a list of job counts grouped by type and status
        jobs = Job.objects.filter(status__in=['PENDING', 'QUEUED', 'RUNNING'])
        jobs = jobs.values('job_type_id', 'status')
        jobs = jobs.annotate(count=models.Count('job_type'))

        # Create a new load model per job type
        job_loads = {}
        measured = timezone.now()
        for job in jobs.iterator():
            job_type_id = job['job_type_id']
            if job_type_id not in job_loads:
                job_load = JobLoad(job_type_id=job_type_id, measured=measured)
                job_load.pending_count = 0
                job_load.queued_count = 0
                job_load.running_count = 0
                job_load.total_count = 0
                job_loads[job_type_id] = job_load
            job_load = job_loads[job_type_id]

            status = job['status']
            count = job['count']
            if status == 'PENDING':
                job_load.pending_count += count
            elif status == 'QUEUED':
                job_load.queued_count += count
            elif status == 'RUNNING':
                job_load.running_count += count
            else:
                logger.error('Unexpected job discovered with status: %s', status)
            job_load.total_count += count

        if job_loads:
            # Save all the database models
            JobLoad.objects.bulk_create(job_loads.values())
        else:
            # Save an empty record as a place holder
            JobLoad(measured=measured, pending_count=0, queued_count=0, running_count=0, total_count=0).save()

    def get_job_loads(self, started=None, ended=None, job_type_ids=None, job_type_names=None, job_type_categories=None,
                      job_type_priorities=None, order=None):
        """Returns a list of job loads within the given time range.

        :param started: Query jobs updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query jobs updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param job_type_ids: Query jobs of the type associated with the identifier.
        :type job_type_ids: list[int]
        :param job_type_names: Query jobs of the type associated with the name.
        :type job_type_names: list[str]
        :param job_type_categories: Query jobs of the type associated with the category.
        :type job_type_categories: list[str]
        :param job_type_priorities: Query jobs of the type associated with the priority.
        :type job_type_priorities: list[int]
        :param order: A list of fields to control the sort order.
        :type order: list[str]
        :returns: The list of job loads that match the time range.
        :rtype: list[:class:`queue.models.JobLoad`]
        """

        # Fetch a list of job loads
        job_loads = JobLoad.objects.all().select_related('job_type')

        # Apply time range filtering
        if started:
            job_loads = job_loads.filter(measured__gte=started)
        if ended:
            job_loads = job_loads.filter(measured__lte=ended)

        # Apply additional filters
        if job_type_ids:
            job_loads = job_loads.filter(job_type_id__in=job_type_ids)
        if job_type_names:
            job_loads = job_loads.filter(job_type__name__in=job_type_names)
        if job_type_categories:
            job_loads = job_loads.filter(job_type__category__in=job_type_categories)
        if job_type_priorities:
            job_loads = job_loads.filter(job_type__priority__in=job_type_priorities)

        # Apply sorting
        if order:
            job_loads = job_loads.order_by(*order)
        else:
            job_loads = job_loads.order_by('measured')
        return job_loads

    def group_by_time(self, job_loads):
        """Groups the given job loads by job type.

        :param job_loads: Query jobs updated after this amount of time.
        :type job_loads: list[:class:`queue.models.JobLoad`]
        :returns: A list of job loads grouped by job type.
        :rtype: list[:class:`queue.models.JobLoadGroup`]
        """
        results = []
        for job_load in job_loads:
            if not results or results[-1].time != job_load.measured:
                results.append(JobLoadGroup(job_load.measured))
            results[-1].pending_count += job_load.pending_count
            results[-1].queued_count += job_load.queued_count
            results[-1].running_count += job_load.running_count
        return results


class JobLoad(models.Model):
    """Represents the load counts for each job type at various points in time.

    :keyword job_type: The type of job being measured.
    :type job_type: :class:`django.db.models.ForeignKey`
    :keyword measured: When the counts were actually measured.
    :type measured: :class:`django.db.models.DateTimeField`

    :keyword pending_count: The number of jobs in pending status for the type.
    :type pending_count: :class:`django.db.models.IntegerField`
    :keyword queued_count: The number of jobs in queued status for the type.
    :type queued_count: :class:`django.db.models.IntegerField`
    :keyword running_count: The number of jobs in running status for the type.
    :type running_count: :class:`django.db.models.IntegerField`
    :keyword total_count: The number of jobs in pending, queued, or running status for the type.
    :type total_count: :class:`django.db.models.IntegerField`
    """

    job_type = models.ForeignKey('job.JobType', on_delete=models.PROTECT, blank=True, null=True)
    measured = models.DateTimeField(db_index=True)

    pending_count = models.IntegerField()
    queued_count = models.IntegerField()
    running_count = models.IntegerField()
    total_count = models.IntegerField()

    objects = JobLoadManager()

    class Meta(object):
        """meta information for the db"""
        db_table = 'job_load'


class QueueEventProcessor(object):
    """Base class used to process queue events."""
    __metaclass__ = abc.ABCMeta

    def process_queued(self, job_exe, is_initial):
        """Callback when a new job execution is queued that sub-classes have registered to process.

        :param job_exe: The new job execution that requires processing.
        :type job_exe: :class:`job.models.JobExecution`
        :param is_initial: Whether or not this is the first time the associated job has been queued.
        :type is_initial: bool
        """
        raise NotImplemented()

    def process_completed(self, job_exe):
        """Callback when an existing job execution completed successfully that sub-classes have registered to process.

        :param job_exe: The new job execution that requires processing.
        :type job_exe: :class:`job.models.JobExecution`
        """
        raise NotImplemented()

    def process_failed(self, job_exe):
        """Callback when an existing job execution failed that sub-classes have registered to process.

        :param job_exe: The new job execution that requires processing.
        :type job_exe: :class:`job.models.JobExecution`
        """
        raise NotImplemented()


class QueueStatus(object):
    """Represents queue status statistics.

    :keyword job_type: The job type being counted.
    :type job_type: :class:`job.models.JobType`
    :keyword count: The number of job executions running for the associated job type.
    :type count: int
    :keyword longest_queued: The date/time of the last queued job execution for the associated job type.
    :type longest_queued: datetime.datetime
    :keyword highest_priority: The priority of the most important job execution for the associated job type.
    :type highest_priority: int
    """
    def __init__(self, job_type, count=0, longest_queued=None, highest_priority=100):
        self.job_type = job_type
        self.count = count
        self.longest_queued = longest_queued
        self.highest_priority = highest_priority


class QueueManager(models.Manager):
    """Provides additional methods for managing the queue
    """

    # List of queue event processor class definitions
    _processors = []

    def get_queue(self, order_mode, ignore_job_type_ids=None):
        """Returns the list of queue models sorted according to their priority first, and then according to the provided
        mode

        :param order_mode: The mode determining how to order the queue (FIFO or LIFO)
        :type order_mode: string
        :param ignore_job_type_ids: The list of job type IDs to ignore
        :type ignore_job_type_ids: list
        :returns: The list of queue models
        :rtype: list[:class:`queue.models.Queue`]
        """

        query = self.all()

        if ignore_job_type_ids:
            query = query.exclude(job_type_id__in=ignore_job_type_ids)

        if order_mode == QUEUE_ORDER_FIFO:
            return query.order_by('priority', 'queued')
        elif order_mode == QUEUE_ORDER_LIFO:
            return query.order_by('priority', '-queued')
        return query.order_by('priority')

    def get_queue_status(self):
        """Returns the current status of the queue with statistics broken down by job type.

        :returns: A list of each job type with calculated statistics.
        :rtype: list[:class:`queue.models.QueueStatus`]
        """

        status_dicts = Queue.objects.values(*['job_type__%s' % f for f in JobType.BASE_FIELDS])
        status_dicts = status_dicts.annotate(count=models.Count('job_type'), longest_queued=models.Min('queued'),
                                             highest_priority=models.Min('priority'))
        status_dicts = status_dicts.order_by('job_type__is_paused', 'highest_priority', 'longest_queued')

        # Convert each result to a real job type model with added statistics
        results = []
        for status_dict in status_dicts:
            job_type_dict = {f: status_dict['job_type__%s' % f] for f in JobType.BASE_FIELDS}
            job_type = JobType(**job_type_dict)

            status = QueueStatus(job_type, status_dict['count'], status_dict['longest_queued'],
                                 status_dict['highest_priority'])
            results.append(status)
        return results

    @transaction.atomic
    def handle_job_cancellation(self, job_id, when):
        """Handles the cancellation of a job. All database changes occur in an atomic transaction.

        :param job_id: The ID of the job to be canceled
        :type job_id: int
        :param when: When the job was canceled
        :type when: :class:`datetime.datetime`
        """

        # Acquire model lock on latest job execution
        job_exe_qry = JobExecution.objects.select_for_update().defer('stdout', 'stderr').filter(job_id=job_id)
        job_exe = job_exe_qry.order_by('-created').first()

        # Acquire model lock on job
        job = Job.objects.get_locked_job(job_id)

        # Get latest job execution again to ensure no new job execution was just created
        job_exe_2 = JobExecution.objects.defer('stdout', 'stderr').filter(job_id=job_id).order_by('-created').first()

        # It's possible that a new latest job execution was created between obtaining the job_exe and job locks above.
        # If this happens (should be quite rare), we need to abort the cancellation
        job_exe_id = job_exe.id if job_exe else None
        job_exe_2_id = job_exe_2.id if job_exe_2 else None
        if job_exe_id != job_exe_2_id:
            raise Exception('Job could not be canceled due to a rare status conflict. Please try again.')

        if not job.can_be_canceled:
            raise Exception('Job cannot be canceled when in status %s' % job.status)

        if job_exe and not job_exe.is_finished:
            # Stop the current job execution, removing it from the queue if applicable
            if job_exe.status == 'QUEUED':
                Queue.objects.filter(job_exe_id=job_exe.id).delete()
            JobExecution.objects.update_status([job_exe], 'CANCELED', when)
        else:
            # Latest job execution was finished, so just mark the job as CANCELED
            Job.objects.update_status([job], 'CANCELED', when)

        # If this job is in a recipe, update dependent jobs so that they are BLOCKED
        handler = Recipe.objects.get_recipe_handler_for_job(job.id)
        if handler:
            jobs_to_blocked = handler.get_blocked_jobs()
            Job.objects.update_status(jobs_to_blocked, 'BLOCKED', when)

    @transaction.atomic
    def handle_job_completion(self, job_exe_id, when, tasks):
        """Handles the successful completion of a job. All database changes occur in an atomic transaction.

        :param job_exe_id: The ID of the job execution that successfully completed
        :type job_exe_id: int
        :param when: When the job execution was completed
        :type when: :class:`datetime.datetime`
        :param tasks: The list of this job's tasks
        :type tasks: [:class:`job.tasks.base_task.Task`]
        """

        job_exe = JobExecution.objects.get_locked_job_exe(job_exe_id)
        if job_exe.status != 'RUNNING':
            # If this job execution is no longer running, ignore completion
            return
        job_exe.job = Job.objects.get_locked_job(job_exe.job_id)
        for task in tasks:
            task.populate_job_exe_model(job_exe)
        JobExecution.objects.complete_job_exe(job_exe, when)

        # Execute any registered processors from other applications
        for processor_class in self._processors:
            try:
                processor = processor_class()
                processor.process_completed(job_exe)
            except:
                logger.exception('Unable to call queue processor for completed job execution: %s -> %s',
                                 processor_class, job_exe_id)

        # If this job is in a recipe, queue any jobs in the recipe that have their job dependencies completed
        handler = Recipe.objects.get_recipe_handler_for_job(job_exe.job_id)
        if handler:
            if not job_exe.job.is_superseded:  # Do not queue dependent jobs for superseded jobs
                jobs_to_queue = []
                for job_tuple in handler.get_existing_jobs_to_queue():
                    job = job_tuple[0]
                    job_data = job_tuple[1]
                    try:
                        Job.objects.populate_job_data(job, job_data)
                    except InvalidData as ex:
                        raise Exception('Scale created invalid job data: %s' % str(ex))
                    jobs_to_queue.append(job)
                if jobs_to_queue:
                    self._queue_jobs(jobs_to_queue)
            if handler.is_completed():
                Recipe.objects.complete(handler.recipe.id, when)

    @transaction.atomic
    def handle_job_failure(self, job_exe_id, when, tasks, error=None):
        """Handles the failure of a job execution. If the job has tries remaining, it is put back on the queue.
        Otherwise it is marked failed. All database changes occur in an atomic transaction.

        :param job_exe_id: The ID of the job execution that failed
        :type job_exe_id: int
        :param when: When the failure occurred
        :type when: :class:`datetime.datetime`
        :param tasks: The list of this job's tasks
        :type tasks: [:class:`job.tasks.base_task.Task`]
        :param error: The error that caused the failure
        :type error: :class:`error.models.Error`
        """

        if not error:
            error = Error.objects.get_unknown_error()

        job_exe = JobExecution.objects.get_locked_job_exe(job_exe_id)
        if job_exe.status != 'RUNNING':
            # If this job execution is no longer running, ignore failure
            return
        job_exe.job = Job.objects.get_locked_job(job_exe.job_id)
        for task in tasks:
            task.populate_job_exe_model(job_exe)
        JobExecution.objects.update_status([job_exe], 'FAILED', when, error)
        # TODO: extra save here to capture task info, re-work this as part of the architecture refactor
        job_exe.save()

        # Execute any registered processors from other applications
        for processor_class in self._processors:
            try:
                processor = processor_class()
                processor.process_failed(job_exe)
            except:
                logger.exception('Unable to call queue processor for failed job execution: %s -> %s', processor_class,
                                 job_exe_id)

        # Re-try job if error supports re-try and there are more tries left
        retry = error.should_be_retried and job_exe.job.num_exes < job_exe.job.max_tries
        # Also re-try long running jobs
        retry = retry or job_exe.job.job_type.is_long_running
        # Do not re-try superseded jobs
        retry = retry and not job_exe.job.is_superseded

        if retry:
            self._queue_jobs([job_exe.job])
        else:
            # If this job is in a recipe, update dependent jobs so that they are BLOCKED
            handler = Recipe.objects.get_recipe_handler_for_job(job_exe.job_id)
            if handler:
                jobs_to_blocked = handler.get_blocked_jobs()
                Job.objects.update_status(jobs_to_blocked, 'BLOCKED', when)

    @transaction.atomic
    def queue_new_job(self, job_type, data, event, configuration=None):
        """Creates a new job for the given type and data. The new job is immediately placed on the queue. The new job,
        job_exe, and queue models are saved in the database in an atomic transaction.

        :param job_type: The type of the new job to create and queue
        :type job_type: :class:`job.models.JobType`
        :param data: The job data to run on
        :type data: :class:`job.configuration.data.job_data.JobData`
        :param event: The event that triggered the creation of this job
        :type event: :class:`trigger.models.TriggerEvent`
        :param configuration: The optional initial execution configuration
        :type configuration: :class:`job.configuration.json.execution.exe_config.ExecutionConfiguration`
        :returns: The new queued job
        :rtype: :class:`job.models.Job`

        :raises job.configuration.data.exceptions.InvalidData: If the job data is invalid
        """

        job = Job.objects.create_job(job_type, event)
        if not configuration:
            configuration = ExecutionConfiguration()
        job.configuration = configuration.get_dict()
        job.save()

        # No lock needed for this job since it doesn't exist outside this transaction yet
        Job.objects.populate_job_data(job, data)
        self._queue_jobs([job])

        return job

    # TODO: once Django user auth is used, have the user information passed into here
    @transaction.atomic
    def queue_new_job_for_user(self, job_type, data):
        """Creates a new job for the given type and data at the request of a user. The new job is immediately placed on
        the queue. The given job_type model must have already been saved in the database (it must have an ID). The new
        job, event, job_exe, and queue models are saved in the database in an atomic transaction. If the data is
        invalid, a :class:`job.configuration.data.exceptions.InvalidData` will be thrown.

        :param job_type: The type of the new job to create and queue
        :type job_type: :class:`job.models.JobType`
        :param data: JSON description defining the job data to run on
        :type data: dict
        :returns: The ID of the new job and the ID of the job execution
        :rtype: tuple of (int, int)
        """

        description = {'user': 'Anonymous'}
        event = TriggerEvent.objects.create_trigger_event('USER', None, description, timezone.now())

        job_id = self.queue_new_job(job_type, JobData(data), event).id
        job_exe = JobExecution.objects.get(job_id=job_id, status='QUEUED')
        return job_id, job_exe.id

    @transaction.atomic
    def queue_new_recipe(self, recipe_type, data, event, superseded_recipe=None, delta=None, superseded_jobs=None,
                         priority=None):
        """Creates a new recipe for the given type and data. and queues any of its jobs that are ready to run. If the
        new recipe is superseding an old recipe, superseded_recipe, delta, and superseded_jobs must be provided and the
        caller must have obtained a model lock on all job models in superseded_jobs and on the superseded_recipe model.
        All database changes occur in an atomic transaction.

        :param recipe_type: The type of the new recipe to create
        :type recipe_type: :class:`recipe.models.RecipeType`
        :param data: The recipe data to run on, should be None if superseded_recipe is provided
        :type data: :class:`recipe.data.recipe_data.RecipeData`
        :param event: The event that triggered the creation of this recipe
        :type event: :class:`trigger.models.TriggerEvent`
        :param superseded_recipe: The recipe that the created recipe is superseding, possibly None
        :type superseded_recipe: :class:`recipe.models.Recipe`
        :param delta: If not None, represents the changes between the old recipe to supersede and the new recipe
        :type delta: :class:`recipe.handlers.graph_delta.RecipeGraphDelta`
        :param superseded_jobs: If not None, represents the job models (stored by job name) of the old recipe to
            supersede
        :type superseded_jobs: {string: :class:`job.models.Job`}
        :param priority: An optional argument to reset the priority of associated jobs before they are queued
        :type priority: int
        :returns: A handler for the new recipe
        :rtype: :class:`recipe.handlers.handler.RecipeHandler`

        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeData`: If the recipe data is invalid
        """

        handler = Recipe.objects.create_recipe(recipe_type, data, event, superseded_recipe, delta, superseded_jobs)
        jobs_to_queue = []
        for job_tuple in handler.get_existing_jobs_to_queue():
            job = job_tuple[0]
            job_data = job_tuple[1]
            try:
                Job.objects.populate_job_data(job, job_data)
            except InvalidData as ex:
                raise Exception('Scale created invalid job data: %s' % str(ex))
            jobs_to_queue.append(job)
        if jobs_to_queue:
            self._queue_jobs(jobs_to_queue, priority)

        return handler

    # TODO: once Django user auth is used, have the user information passed into here
    @transaction.atomic
    def queue_new_recipe_for_user(self, recipe_type, data):
        """Creates a new recipe for the given type and data at the request of a user.

        The new jobs in the recipe with no dependencies on other jobs are immediately placed on the queue. The given
        event model must have already been saved in the database (it must have an ID). All database changes occur in an
        atomic transaction.

        :param recipe_type: The type of the new recipe to create
        :type recipe_type: :class:`recipe.models.RecipeType`
        :param data: The recipe data to run on, should be None if superseded_recipe is provided
        :type data: :class:`recipe.data.recipe_data.RecipeData`
        :returns: A handler for the new recipe
        :rtype: :class:`recipe.handlers.handler.RecipeHandler`

        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeData`: If the recipe data is invalid
        """

        description = {'user': 'Anonymous'}
        event = TriggerEvent.objects.create_trigger_event('USER', None, description, timezone.now())

        return self.queue_new_recipe(recipe_type, data, event)

    def register_processor(self, processor_class):
        """Registers the given processor class to be called when job executions change status.

        Processors from other applications can be registered during their ready() method.

        :param processor_class: The processor class to invoke when the associated status change occurs.
        :type processor_class: :class:`job.clock.ClockProcessor`
        """
        logger.debug('Registering queue processor: %s', processor_class)
        self._processors.append(processor_class)

    @transaction.atomic
    def requeue_jobs(self, job_ids, priority=None):
        """Re-queues the jobs with the given IDs. Any job that is not in a valid state for being re-queued or is
        superseded will be ignored. All database changes will occur within an atomic transaction.

        :param job_ids: The IDs of the jobs to re-queue
        :type job_ids: [int]
        :param priority: An optional argument to reset the jobs' priority before they are queued
        :type priority: int
        """

        jobs_to_requeue = Job.objects.get_locked_jobs(job_ids)
        all_valid_job_ids = []
        jobs_to_queue = []
        jobs_to_blocked = []
        jobs_to_pending = []
        for job in jobs_to_requeue:
            if not job.is_ready_to_requeue or job.is_superseded:
                continue
            all_valid_job_ids.append(job.id)
            if job.num_exes == 0:
                # Never been queued before, job should either be PENDING or BLOCKED depending on parent jobs
                # Assume BLOCKED and it will get switched to PENDING later if needed
                jobs_to_blocked.append(job)
            else:
                # Queued before, go back on queue
                jobs_to_queue.append(job)

        # Update jobs that are being re-queued
        if jobs_to_queue:
            Job.objects.increment_max_tries(jobs_to_queue)
            self._queue_jobs(jobs_to_queue, priority)
        when = timezone.now()
        if jobs_to_blocked:
            Job.objects.update_status(jobs_to_blocked, 'BLOCKED', when)

        # Update dependent recipe jobs (with model locks) that should now go back to PENDING
        for handler in Recipe.objects.get_recipe_handlers_for_jobs(all_valid_job_ids):
            jobs_to_pending.extend(handler.get_pending_jobs())
        if jobs_to_pending:
            Job.objects.update_status(jobs_to_pending, 'PENDING', when)

    @transaction.atomic
    def schedule_job_executions(self, framework_id, job_executions, workspaces):
        """Schedules the given job executions on the provided nodes and resources. The corresponding queue models will
        be deleted from the database. All database changes occur in an atomic transaction.

        :param framework_id: The scheduling framework ID
        :type framework_id: string
        :param job_executions: A list of queued job executions that have been given nodes and resources on which to run
        :type job_executions: list[:class:`queue.job_exe.QueuedJobExecution`]
        :param workspaces: A dict of all workspaces stored by name
        :type workspaces: {string: :class:`storage.models.Workspace`}
        :returns: The scheduled job executions
        :rtype: list[:class:`job.execution.job_exe.RunningJobExecution`]
        """

        if not job_executions:
            return []

        job_exe_ids = []
        for job_execution in job_executions:
            job_exe_ids.append(job_execution.id)

        # Lock corresponding job executions
        job_exes = {}
        for job_exe in JobExecution.objects.select_for_update().filter(id__in=job_exe_ids).order_by('id'):
            job_exes[job_exe.id] = job_exe

        # Set up job executions to schedule
        executions_to_schedule = []
        for job_execution in job_executions:
            node_id = job_execution.provided_node_id
            resources = job_execution.provided_resources
            input_file_size = job_execution.input_file_size
            job_exe = job_exes[job_execution.id]

            # Ignore executions that are no longer queued (executions may have been changed since queue model was last
            # queried)
            if job_exe.status != 'QUEUED':
                continue

            executions_to_schedule.append((job_exe, node_id, resources, input_file_size))

        # Schedule job executions
        scheduled_job_exes = []
        job_exe_ids_scheduled = []
        for job_exe in JobExecution.objects.schedule_job_executions(framework_id, executions_to_schedule, workspaces):
            scheduled_job_exes.append(RunningJobExecution(job_exe))
            job_exe_ids_scheduled.append(job_exe.id)

        # Clear the scheduled job executions from the queue
        Queue.objects.filter(job_exe_id__in=job_exe_ids_scheduled).delete()

        return scheduled_job_exes

    def _queue_jobs(self, jobs, priority=None):
        """Queues the given jobs and returns the new queued job executions. The caller must have obtained model locks on
        the job models. Any jobs that are not in a valid status for being queued, are without job data, or are
        superseded will be ignored. All jobs should have their related job_type and job_type_rev models populated.

        :param jobs: The jobs to put on the queue
        :type jobs: [:class:`job.models.Job`]
        :param priority: An optional argument to reset the jobs' priority before they are queued
        :type priority: int
        :returns: The new queued job execution models
        :rtype: [:class:`job.models.JobExecution`]
        """

        when_queued = timezone.now()

        job_exes = Job.objects.queue_jobs(jobs, when_queued, priority)

        # Execute any registered processors from other applications
        for processor_class in self._processors:
            processor = processor_class()
            for job_exe in job_exes:
                processor.process_queued(job_exe, job_exe.job.num_exes == 1)

        queues = []
        for job_exe in job_exes:
            queue = Queue()
            queue.job_exe = job_exe
            queue.job = job_exe.job
            queue.job_type = job_exe.job.job_type
            queue.priority = job_exe.job.priority
            queue.input_file_size = job_exe.job.disk_in_required if job_exe.job.disk_in_required else 0.0
            queue.configuration = job_exe.job.configuration
            queue.resources = job_exe.job.get_resources().get_json().get_dict()
            queue.queued = when_queued
            queues.append(queue)

        if not queues:
            return []

        self.bulk_create(queues)
        return job_exes


class Queue(models.Model):
    """Represents a job that is queued to be run on a node

    :keyword job_exe: The job execution that has been queued
    :type job_exe: :class:`django.db.models.ForeignKey`
    :keyword job: The job that has been queued
    :type job: :class:`django.db.models.ForeignKey`
    :keyword job_type: The type of this job execution
    :type job_type: :class:`django.db.models.ForeignKey`

    :keyword priority: The priority of the job (lower number is higher priority)
    :type priority: :class:`django.db.models.IntegerField`
    :keyword input_file_size: The amount of disk space in MiB required for input files for this job
    :type input_file_size: :class:`django.db.models.FloatField`

    :keyword configuration: JSON description describing the configuration for how the job should be run
    :type configuration: :class:`django.contrib.postgres.fields.JSONField`
    :keyword resources: JSON description describing the resources required for this job
    :type resources: :class:`django.contrib.postgres.fields.JSONField`

    :keyword created: When the queue model was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword queued: When the job execution was placed onto the queue
    :type queued: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the queue model was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`
    """

    job_exe = models.OneToOneField('job.JobExecution', primary_key=True, on_delete=models.PROTECT)
    job = models.ForeignKey('job.Job', on_delete=models.PROTECT)
    job_type = models.ForeignKey('job.JobType', on_delete=models.PROTECT)

    priority = models.IntegerField(db_index=True)
    input_file_size = models.FloatField()

    configuration = django.contrib.postgres.fields.JSONField(default=dict)
    resources = django.contrib.postgres.fields.JSONField(default=dict)

    created = models.DateTimeField(auto_now_add=True)
    queued = models.DateTimeField()
    last_modified = models.DateTimeField(auto_now=True)

    objects = QueueManager()

    def get_resources(self):
        """Returns the resources required by this job execution

        :returns: The required resources
        :rtype: :class:`node.resources.node_resources.NodeResources`
        """

        return Resources(self.resources).get_node_resources()

    class Meta(object):
        """meta information for the db"""
        db_table = 'queue'
