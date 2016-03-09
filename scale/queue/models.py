"""Defines the database model for a queue entry"""
from __future__ import unicode_literals

import abc
import logging

import django.utils.timezone as timezone
from django.db import models, transaction

from error.models import Error
from job.configuration.data.exceptions import InvalidData, StatusError
from job.configuration.data.job_data import JobData
from job.execution.running.job_exe import RunningJobExecution
from job.models import Job, JobType
from job.models import JobExecution
from recipe.models import Recipe
from trigger.models import TriggerEvent

logger = logging.getLogger(__name__)


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


class QueueManager(models.Manager):
    """Provides additional methods for managing the queue
    """

    # List of queue event processor class definitions
    _processors = []

    # TODO: Remove this once the UI migrates to job load
    def get_current_queue_depth(self):
        """Returns the current queue depth, both for each job type and for each priority level

        :returns: Tuple of two dicts where the first has each job type ID map to its depth count and the second has each
            priority level map to its depth count
        :rtype: tuple of ({int: int}, {int: int})
        """

        depth_by_job_type = {}
        depth_by_priority = {}
        depth_qry = Queue.objects.values('job_type_id', 'priority')
        depth_qry = depth_qry.annotate(count=models.Count('job_type'))

        for depth_record in depth_qry:
            job_type_id = depth_record['job_type_id']
            priority = depth_record['priority']
            count = depth_record['count']
            if job_type_id in depth_by_job_type:
                depth_by_job_type[job_type_id] += count
            else:
                depth_by_job_type[job_type_id] = count
            if priority in depth_by_priority:
                depth_by_priority[priority] += count
            else:
                depth_by_priority[priority] = count

        return (depth_by_job_type, depth_by_priority)

    # TODO: Remove this once the UI migrates to job load
    def get_historical_queue_depth(self, started, ended):
        """Returns the historical queue depth for the given range. The queue depth is returned as a dict with three
        keys: a "job_types" array that lists the job types that had a depth during the time range, a "priorities" array
        that contains the priority levels that had a depth, and a "queue_depth" array with the total depth, depth by job
        type, and depth by priority for each time that the queue depth was measured.

        :param started: the start of the time range
        :type started: :class:`datetime.datetime`
        :param ended: the end of the time range
        :type ended: :class:`datetime.datetime`
        :returns: dict with the queue depth measurements for the given time range
        :rtype: dict
        """

        job_type_qry = QueueDepthByJobType.objects.filter(depth_time__gte=started, depth_time__lte=ended)
        job_type_qry = job_type_qry.select_related('job_type').order_by('depth_time')
        priority_qry = QueueDepthByPriority.objects.filter(depth_time__gte=started, depth_time__lte=ended)
        priority_qry = priority_qry.select_related('job_type').order_by('depth_time')

        # Process query results into dict
        job_types = []
        priorities = []
        queue_depth_dict = {}  # time -> ({job type ID: depth count}, {priority: depth count})
        depth_times = []
        self._process_job_type_depths(job_type_qry, job_types, queue_depth_dict, depth_times)
        self._process_priority_depths(priority_qry, priorities, queue_depth_dict)
        queue_depths = self._process_queue_depths(job_types, priorities, queue_depth_dict, depth_times)

        return {'job_types': job_types, 'priorities': priorities, 'queue_depths': queue_depths}

    def get_queue(self):
        """Returns the list of queue models sorted according to their scheduling priority

        :returns: The list of queue models
        :rtype: list[:class:`queue.models.Queue`]
        """

        return Queue.objects.order_by('priority', 'queued').iterator()

    def get_queue_status(self):
        """Returns the current status of the queue, which is a list of dicts with each dict containing a job type and
        version with overall stats for that type

        :returns: The list of each job type with stats
        :rtype: list of dict
        """

        status_qry = Queue.objects.values('job_type__name', 'job_type__version', 'job_type__is_paused')
        status_qry = status_qry.annotate(count=models.Count('job_type'), longest_queued=models.Min('queued'),
                                         highest_priority=models.Min('priority'))
        status_qry = status_qry.order_by('job_type__is_paused', 'highest_priority', 'longest_queued')

        # Remove double underscores
        for entry in status_qry:
            name = entry['job_type__name']
            version = entry['job_type__version']
            is_paused = entry['job_type__is_paused']
            del entry['job_type__name']
            del entry['job_type__version']
            del entry['job_type__is_paused']
            entry['job_type_name'] = name
            entry['job_type_version'] = version
            entry['is_job_type_paused'] = is_paused

        return status_qry

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
            self._handle_job_finished(job_exe)
        else:
            # Latest job execution was finished, so just mark the job as CANCELED
            Job.objects.update_status([job], 'CANCELED', when)

        # If this job is in a recipe, update dependent jobs so that they are BLOCKED
        handler = Recipe.objects.get_recipe_handler_for_job(job.id)
        if handler:
            jobs_to_blocked = handler.get_blocked_jobs()
            Job.objects.update_status(jobs_to_blocked, 'BLOCKED', when)

    @transaction.atomic
    def handle_job_completion(self, job_exe_id, when):
        """Handles the successful completion of a job. All database changes occur in an atomic transaction.

        :param job_exe_id: The ID of the job execution that successfully completed
        :type job_exe_id: int
        :param when: When the job execution was completed
        :type when: :class:`datetime.datetime`
        """

        job_exe = JobExecution.objects.get_locked_job_exe(job_exe_id)
        if job_exe.status != 'RUNNING':
            # If this job execution is no longer running, ignore completion
            return
        job_exe.job = Job.objects.get_locked_job(job_exe.job_id)
        JobExecution.objects.complete_job_exe(job_exe, when)

        self._handle_job_finished(job_exe)

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
                Recipe.objects.complete(handler.recipe_id, when)

    @transaction.atomic
    def handle_job_failure(self, job_exe_id, when, error=None):
        """Handles the failure of a job execution. If the job has tries remaining, it is put back on the queue.
        Otherwise it is marked failed. All database changes occur in an atomic transaction.

        :param job_exe_id: The ID of the job execution that failed
        :type job_exe_id: int
        :param when: When the failure occurred
        :type when: :class:`datetime.datetime`
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
        JobExecution.objects.update_status([job_exe], 'FAILED', when, error)

        self._handle_job_finished(job_exe)

        # Execute any registered processors from other applications
        for processor_class in self._processors:
            try:
                processor = processor_class()
                processor.process_failed(job_exe)
            except:
                logger.exception('Unable to call queue processor for failed job execution: %s -> %s', processor_class,
                                 job_exe_id)

        # Re-queue job if a system error occurred and there are more tries left
        requeue = error.category == 'SYSTEM' and job_exe.job.num_exes < job_exe.job.max_tries
        # Also re-queue long running jobs
        requeue = requeue or job_exe.job.job_type.is_long_running
        if requeue:
            self._queue_jobs([job_exe.job])

        # If this job is in a recipe, update dependent jobs so that they are BLOCKED
        handler = Recipe.objects.get_recipe_handler_for_job(job_exe.job_id)
        if handler:
            jobs_to_blocked = handler.get_blocked_jobs()
            Job.objects.update_status(jobs_to_blocked, 'BLOCKED', when)

    @transaction.atomic
    def queue_new_job(self, job_type, data, event):
        """Creates a new job for the given type and data. The new job is immediately placed on the queue. The given
        job_type model must have already been saved in the database (it must have an ID). The given event model must
        have already been saved in the database (it must have an ID). The new job, job_exe, and queue models are saved
        in the database in an atomic transaction. If the data is invalid, a
        :class:`job.configuration.data.exceptions.InvalidData` will be thrown.

        :param job_type: The type of the new job to create and queue
        :type job_type: :class:`job.models.JobType`
        :param data: JSON description defining the job data to run on
        :type data: dict
        :param event: The event that triggered the creation of this job
        :type event: :class:`trigger.models.TriggerEvent`
        :returns: The ID of the new job and the ID of the job execution
        :rtype: int
        :raises job.configuration.data.exceptions.InvalidData: If the job data is invalid
        """

        job = Job.objects.create_job(job_type, event)
        job.save()

        # No lock needed for this job since it doesn't exist outside this transaction yet
        Job.objects.populate_job_data(job, JobData(data))
        self._queue_jobs([job])

        return job.id

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

        job_id = self.queue_new_job(job_type, data, event)
        job_exe = JobExecution.objects.get(job_id=job_id, status='QUEUED')
        return job_id, job_exe.id

    @transaction.atomic
    def queue_new_recipe(self, recipe_type, data, event):
        """Creates a new recipe for the given type and data. The new jobs in the recipe with no dependencies on other
        jobs are immediately placed on the queue. The given recipe_type model must have already been saved in the
        database (it must have an ID). The given event model must have already been saved in the database (it must have
        an ID). All database changes occur in an atomic transaction.

        :param recipe_type: The type of the new recipe to create
        :type recipe_type: :class:`recipe.models.RecipeType`
        :param data: JSON description defining the recipe data to run on
        :type data: dict
        :param event: The event that triggered the creation of this recipe
        :type event: :class:`trigger.models.TriggerEvent`
        :returns: The ID of the new recipe
        :rtype: int
        :raises InvalidData: If the recipe data is invalid
        """

        handler = Recipe.objects.create_recipe(recipe_type, event, data)
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

        return handler.recipe_id

    # TODO: once Django user auth is used, have the user information passed into here
    @transaction.atomic
    def queue_new_recipe_for_user(self, recipe_type, data):
        """Creates a new recipe for the given type and data at the request of a user.

        The new jobs in the recipe with no dependencies on other jobs are immediately placed on the queue. The given
        event model must have already been saved in the database (it must have an ID). All database changes occur in an
        atomic transaction.

        :param recipe_type: The type of the new recipe to create
        :type recipe_type: :class:`recipe.models.RecipeType`
        :param data: JSON description defining the recipe data to run on
        :type data: dict
        :returns: The ID of the new recipe
        :rtype: int
        :raises InvalidData: If the recipe data is invalid
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

    # TODO: deprecated, use requeue_jobs() instead
    @transaction.atomic
    def requeue_existing_job(self, job_id):
        """Puts an existing task on the queue to run that has previously been attempted. The given job identifier must
        correspond to an existing model previously saved in the database and the job must have its related job_type
        model. The new job_exe and queue models are saved in the database in an atomic transaction.

        :param job_id: The ID of the job to update
        :type job_id: int
        :returns: The new job execution id or None if one was not created.
        :rtype: int
        :raises InvalidData: If the job data is invalid
        :raises StatusError: If the job is not in a valid state to be queued.
        """

        # Make sure the job is ready to be re-queued
        jobs = Job.objects.get_locked_jobs([job_id])
        if not jobs:
            raise Job.DoesNotExist
        job = jobs[0]
        if not job.is_ready_to_requeue:
            raise StatusError

        # Increase the max tries to ensure it can be scheduled
        job.increase_max_tries()
        Job.objects.filter(id=job.id).update(max_tries=job.max_tries)

        when = timezone.now()
        job_exe_id = None
        if job.num_exes == 0:
            # Job has never been queued before, set it to BLOCKED, might be changed to PENDING
            Job.objects.update_status([job], 'BLOCKED', when)
        else:
            # Job has been queued before, so queue it again
            self._queue_jobs([job])
            job_exe = JobExecution.objects.get(job_id=job.id, status='QUEUED')
            job_exe_id = job_exe.id

        # Update dependent recipe jobs (with model locks) that should now go back to PENDING
        handler = Recipe.objects.get_recipe_handler_for_job(job_id)
        if handler:
            jobs_to_pending = handler.get_pending_jobs()
            Job.objects.update_status(jobs_to_pending, 'PENDING', when)
        return job_exe_id

    @transaction.atomic
    def requeue_jobs(self, job_ids, priority=None):
        """Re-queues the jobs with the given IDs. Any job that is not in a valid state for being re-queued will be
        ignored. All database changes will occur within an atomic transaction.

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
            if not job.is_ready_to_requeue:
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
        handlers = Recipe.objects.get_recipe_handlers_for_jobs(all_valid_job_ids)
        for job_id in all_valid_job_ids:
            if job_id in handlers:
                handler = handlers[job_id]
                jobs_to_pending.extend(handler.get_pending_jobs())
        if jobs_to_pending:
            Job.objects.update_status(jobs_to_pending, 'PENDING', when)

    @transaction.atomic
    def schedule_job_executions(self, job_executions):
        """Schedules the given job executions on the provided nodes and resources. The corresponding queue models will
        be deleted from the database. All database changes occur in an atomic transaction.

        :param job_executions: A list of queued job executions that have been provided nodes and resources on which to
            run
        :type job_executions: list[:class:`queue.job_exe.QueuedJobExecution`]
        :returns: The scheduled job executions
        :rtype: list[:class:`job.execution.running.job_exe.RunningJobExecution`]
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
            queue = job_execution.queue
            node = job_execution.provided_node
            resources = job_execution.provided_resources
            job_exe = job_exes[job_execution.id]

            # Ignore executions that are no longer queued (executions may have been changed since queue model was last
            # queried)
            if job_exe.status != 'QUEUED':
                continue

            # Check that resources are sufficient
            if resources.cpus < queue.cpus_required:
                msg = 'Job execution requires %s CPUs and only %s were provided'
                raise Exception(msg % (str(resources.cpus), str(queue.cpus_required)))
            if resources.mem < queue.mem_required:
                msg = 'Job execution requires %s MiB of memory and only %s MiB were provided'
                raise Exception(msg % (str(resources.mem), str(queue.mem_required)))
            if resources.disk_in < queue.disk_in_required:
                msg = 'Job execution requires %s MiB of input disk space and only %s MiB were provided'
                raise Exception(msg % (str(resources.disk_in), str(queue.disk_in_required)))
            if resources.disk_out < queue.disk_out_required:
                msg = 'Job execution requires %s MiB of output disk space and only %s MiB were provided'
                raise Exception(msg % (str(resources.disk_out), str(queue.disk_out_required)))
            if resources.disk_total < queue.disk_total_required:
                msg = 'Job execution requires %s MiB of total disk space and only %s MiB were provided'
                raise Exception(msg % (str(resources.disk_total), str(queue.disk_total_required)))

            executions_to_schedule.append((job_exe, node, resources))

        # Schedule job executions
        scheduled_job_exes = []
        for job_exe in JobExecution.objects.schedule_job_executions(executions_to_schedule):
            scheduled_job_exes.append(RunningJobExecution(job_exe))

        # Clear the job executions from the queue
        Queue.objects.filter(job_exe_id__in=job_exe_ids).delete()

        return scheduled_job_exes

    @transaction.atomic
    def _handle_job_finished(self, job_exe):
        """Handles a job execution finishing (reaching a final status of COMPLETED, FAILED, or CANCELED). The caller
        must have obtained a model lock on the given job_exe model. All database changes occur in an atomic transaction.

        :param job_exe: The job execution that finished
        :type job_exe: :class:`job.models.JobExecution`
        """

        if not job_exe.is_finished:
            raise Exception('Job execution is not finished in status %s' % job_exe.status)

        # Start a cleanup job if this execution requires it
        if job_exe.requires_cleanup:

            if job_exe.cleanup_job:
                raise Exception('Job execution already has a cleanup job')

            cleanup_type = JobType.objects.get_cleanup_job_type()
            data = {
                'version': '1.0',
                'input_data': [{'name': 'Job Exe ID', 'value': str(job_exe.id)}]
            }
            desc = {'job_exe_id': job_exe.id, 'node_id': job_exe.node_id}
            event = TriggerEvent.objects.create_trigger_event('CLEANUP', None, desc, timezone.now())
            cleanup_job_id = Queue.objects.queue_new_job(cleanup_type, data, event)
            job_exe.cleanup_job_id = cleanup_job_id
            job_exe.save()

    def _process_job_type_depths(self, job_type_qry, job_types, queue_depth_dict, depth_times):
        """Processes the queue depths that are split by job type

        :param job_type_qry: the query with the depth results
        :type job_type_qry: :class:`django.db.models.query.QuerySet`
        :param job_types: the list of job types processed
        :type job_types: list
        :param queue_depth_dict: Dict of {time: ({job type ID: count}, {priority: count})}
        :type queue_depth_dict: dict
        :param depth_times: List to populate with ascending depth times
        :type depth_times: list
        """

        job_types_set = set()
        for job_type_depth in job_type_qry:
            if job_type_depth.depth_time in queue_depth_dict:
                job_type_dict = queue_depth_dict[job_type_depth.depth_time][0]
            else:
                job_type_dict = {}
                queue_depth_dict[job_type_depth.depth_time] = (job_type_dict, {})
                depth_times.append(job_type_depth.depth_time)
            # Don't process depths of 0, these are just placeholder values to mark the depth_time
            if job_type_depth.depth:
                if job_type_depth.job_type_id not in job_types_set:
                    job_types.append({'id': job_type_depth.job_type_id, 'name': job_type_depth.job_type.name,
                                      'version': job_type_depth.job_type.version})
                    job_types_set.add(job_type_depth.job_type_id)
                job_type_dict[job_type_depth.job_type_id] = job_type_depth.depth

    def _process_priority_depths(self, priority_qry, priorities, queue_depth_dict):
        """Processes the queue depths that are split by priority. The queue_depth_dict must have already been processed
        by _process_job_type_depths().

        :param priority_qry: the query with the depth results
        :type priority_qry: :class:`django.db.models.query.QuerySet`
        :param priorities: the list of priorities processed
        :type priorities: list
        :param queue_depth_dict: Dict of {time: ({job type ID: count}, {priority: count})}
        :type queue_depth_dict: dict
        """

        priorities_set = set()
        for priority_depth in priority_qry:
            priority_dict = queue_depth_dict[priority_depth.depth_time][1]
            # Don't process depths of 0, these are just placeholder values to mark the depth_time
            if priority_depth.depth:
                if priority_depth.priority not in priorities_set:
                    priorities.append({'priority': priority_depth.priority})
                    priorities_set.add(priority_depth.priority)
                priority_dict[priority_depth.priority] = priority_depth.depth

    def _process_queue_depths(self, job_types, priorities, queue_depth_dict, depth_times):
        """Processes and creates the queue depth list

        :param job_types: the list of job types processed
        :type job_types: list
        :param priorities: the list of priorities processed
        :type priorities: list
        :param queue_depth_dict: Dict of {time: ({job type ID: count}, {priority: count})}
        :type queue_depth_dict: dict
        :param depth_times: List with ascending depth times
        :type depth_times: list
        :rtype: list
        :returns: list of queue depth data
        """

        queue_depths = []
        for depth_time in depth_times:
            job_type_dict = queue_depth_dict[depth_time][0]
            priority_dict = queue_depth_dict[depth_time][1]
            job_types_depths = []
            priority_depths = []
            total = 0
            for job_type in job_types:
                depth = 0
                if job_type['id'] in job_type_dict:
                    depth = job_type_dict[job_type['id']]
                job_types_depths.append(depth)
                total += depth
            for priority in priorities:
                depth = 0
                if priority['priority'] in priority_dict:
                    depth = priority_dict[priority['priority']]
                priority_depths.append(depth)
            queue_depths.append({'time': depth_time, 'depth_per_job_type': job_types_depths,
                                 'depth_per_priority': priority_depths, 'total_depth': total})

        return queue_depths

    def _queue_jobs(self, jobs, priority=None):
        """Queues the given jobs and returns the new queued job executions. For jobs that are in recipes, the caller
        must have obtained model locks on all of the corresponding recipe models. For jobs not in recipes, the caller
        must have obtained model locks on the job models. Any jobs not in a valid status for being queued or without job
        data will be ignored. All jobs should have their related job_type and job_type_rev models populated.

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
            queue.job_type = job_exe.job.job_type
            queue.priority = job_exe.job.priority
            if job_exe.job.job_type.name == 'scale-cleanup':
                queue.node_required_id = job_exe.job.event.description['node_id']
            queue.cpus_required = job_exe.job.cpus_required
            queue.mem_required = job_exe.job.mem_required
            queue.disk_in_required = job_exe.job.disk_in_required if job_exe.job.disk_in_required else 0
            queue.disk_out_required = job_exe.job.disk_out_required if job_exe.job.disk_out_required else 0
            queue.disk_total_required = queue.disk_in_required + queue.disk_out_required
            queue.queued = when_queued
            queues.append(queue)

        self.bulk_create(queues)
        return job_exes


class Queue(models.Model):
    """Represents a job that is queued to be run on a node

    :keyword job_exe: The job execution that has been queued
    :type job_exe: :class:`django.db.models.ForeignKey`
    :keyword job_type: The type of this job execution
    :type job_type: :class:`django.db.models.ForeignKey`

    :keyword priority: The priority of the job (lower number is higher priority)
    :type priority: :class:`django.db.models.IntegerField`
    :keyword node_required: The specific node on which this job is required to run
    :type node_required: :class:`django.db.models.ForeignKey`
    :keyword cpus_required: The number of CPUs required for this job
    :type cpus_required: :class:`django.db.models.FloatField`
    :keyword mem_required: The amount of RAM in MiB required for this job
    :type mem_required: :class:`django.db.models.FloatField`
    :keyword disk_in_required: The amount of disk space in MiB required for input files for this job
    :type disk_in_required: :class:`django.db.models.FloatField`
    :keyword disk_out_required: The amount of disk space in MiB required for output (temp work and products) for this
        job
    :type disk_out_required: :class:`django.db.models.FloatField`
    :keyword disk_total_required: The total amount of disk space in MiB required for this job
    :type disk_total_required: :class:`django.db.models.FloatField`

    :keyword created: When the queue model was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword queued: When the job execution was placed onto the queue
    :type queued: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the queue model was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`
    """

    job_exe = models.ForeignKey('job.JobExecution', primary_key=True, on_delete=models.PROTECT)
    job_type = models.ForeignKey('job.JobType', on_delete=models.PROTECT)

    priority = models.IntegerField(db_index=True)
    node_required = models.ForeignKey('node.Node', blank=True, null=True, on_delete=models.PROTECT)
    cpus_required = models.FloatField()
    mem_required = models.FloatField()
    disk_in_required = models.FloatField()
    disk_out_required = models.FloatField()
    disk_total_required = models.FloatField()

    created = models.DateTimeField(auto_now_add=True)
    queued = models.DateTimeField()
    last_modified = models.DateTimeField(auto_now=True)

    objects = QueueManager()

    class Meta(object):
        """meta information for the db"""
        db_table = 'queue'


# TODO: Remove this once the UI migrates to /load
class QueueDepthByJobTypeManager(models.Manager):
    """This class manages the QueueDepthByJobType model
    """

    @transaction.atomic
    def save_depths(self, depth_time, depths):
        """Saves the given queue depth statistics. The new models are saved in the database in an atomic transaction.

        :param depth_time: The time that the depth was measured
        :type depth_time: :class:`datetime.datetime`
        :param depths: Dict with job type IDs mapping to their corresponding depth counts
        :type depths: dict of {int: int}
        """

        if not depths:
            # Save at least one (dummy) model so that it is known that the queue depth was 0 at this time
            depths = {1: 0}

        for job_type_id in depths:
            depth_model = QueueDepthByJobType()
            depth_model.job_type_id = job_type_id
            depth_model.depth_time = depth_time
            depth_model.depth = depths[job_type_id]
            depth_model.save()


# TODO: Remove this once the UI migrates to /load
class QueueDepthByJobType(models.Model):
    """Represents the queue depth counts for each job type at various points in time

    :keyword job_type: The job type
    :type job_type: :class:`django.db.models.ForeignKey`
    :keyword depth_time: When the depth was measured
    :type depth_time: :class:`django.db.models.DateTimeField`
    :keyword depth: The queue depth for this job type at this time
    :type depth: :class:`django.db.models.IntegerField`
    """

    job_type = models.ForeignKey('job.JobType', on_delete=models.PROTECT)
    depth_time = models.DateTimeField(db_index=True)
    depth = models.IntegerField()

    objects = QueueDepthByJobTypeManager()

    class Meta(object):
        """meta information for the db"""
        db_table = 'queue_depth_job_type'


# TODO: Remove this once the UI migrates to /load
class QueueDepthByPriorityManager(models.Manager):
    """This class manages the QueueDepthByPriority model
    """

    @transaction.atomic
    def save_depths(self, depth_time, depths):
        """Saves the given queue depth statistics. The new models are saved in the database in an atomic transaction.

        :param depth_time: The time that the depth was measured
        :type depth_time: :class:`datetime.datetime`
        :param depths: Dict with priorities mapping to their corresponding depth counts
        :type depths: dict of {int: int}
        """

        if not depths:
            # Save at least one (dummy) model so that it is known that the queue depth was 0 at this time
            depths = {1: 0}

        for priority in depths:
            depth_model = QueueDepthByPriority()
            depth_model.priority = priority
            depth_model.depth_time = depth_time
            depth_model.depth = depths[priority]
            depth_model.save()


# TODO: Remove this once the UI migrates to /load
class QueueDepthByPriority(models.Model):
    """Represents the queue depth counts for each priority level at various points in time

    :keyword priority: The priority level
    :type priority: :class:`django.db.models.IntegerField`
    :keyword depth_time: When the depth was measured
    :type depth_time: :class:`django.db.models.DateTimeField`
    :keyword depth: The queue depth for this priority at this time
    :type depth: :class:`django.db.models.IntegerField`
    """

    priority = models.IntegerField()
    depth_time = models.DateTimeField(db_index=True)
    depth = models.IntegerField()

    objects = QueueDepthByPriorityManager()

    class Meta(object):
        """meta information for the db"""
        db_table = 'queue_depth_priority'
