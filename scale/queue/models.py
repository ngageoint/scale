"""Defines the database model for a queue entry"""
from __future__ import unicode_literals

import logging

import django.utils.timezone as timezone
import django.contrib.postgres.fields
from django.db import models, transaction

from error.models import Error
from job.execution.configuration.configurators import QueuedExecutionConfigurator
from job.configuration.data.exceptions import InvalidData
from job.configuration.data.job_data import JobData as JobData_1_0
from job.execution.configuration.json.exe_config import ExecutionConfiguration
from job.data.job_data import JobData
from job.deprecation import JobInterfaceSunset
from job.seed.manifest import SeedManifest
from job.models import Job, JobType
from job.models import JobExecution, JobTypeRevision
from node.resources.json.resources import Resources
from product.models import ProductFile
from recipe.models import Recipe, RecipeTypeRevision
from storage.models import ScaleFile
from trigger.models import TriggerEvent
from data.data.json import data_v6
from messaging.manager import CommandMessageManager
from job.messages.process_job_input import create_process_job_input_messages
from recipe.messages.process_recipe_input import create_process_recipe_input_messages
from util.rest import BadParameter


logger = logging.getLogger(__name__)

QUEUE_ORDER_FIFO = 'FIFO'
QUEUE_ORDER_LIFO = 'LIFO'
DEFAULT_QUEUE_ORDER = QUEUE_ORDER_FIFO


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

    def cancel_queued_jobs(self, job_ids):
        """Marks the queued job executions for the given jobs as canceled

        :param job_ids: The list of job IDs being canceled
        :type job_ids: list
        """

        self.filter(job_id__in=job_ids).update(is_canceled=True)

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

    def queue_jobs(self, jobs, requeue=False, priority=None):
        """Queues the given jobs. The caller must have obtained model locks on the job models in an atomic transaction.
        Any jobs that are not in a valid status for being queued, are without job input, or are superseded will be
        ignored.

        :param jobs: The job models to put on the queue
        :type jobs: list
        :param requeue: Whether this is a re-queue (True) or a first queue (False)
        :type requeue: bool
        :param priority: An optional argument to reset the jobs' priority when they are queued
        :type priority: int
        :returns: The list of job IDs that were successfully QUEUED
        :rtype: list
        """

        when_queued = timezone.now()

        # Set job models to QUEUED
        queued_job_ids = Job.objects.update_jobs_to_queued(jobs, when_queued, requeue=requeue)
        if not queued_job_ids:
            return queued_job_ids  # Done if nothing was queued

        # Retrieve the related job_type, job_type_rev, and batch models for the queued jobs
        queued_jobs = Job.objects.get_jobs_with_related(queued_job_ids)

        # Query for all input files of the queued jobs
        input_files = {}
        input_file_ids = set()
        for job in queued_jobs:
            input_file_ids.update(job.get_job_data().get_input_file_ids())
        if input_file_ids:
            for input_file in ScaleFile.objects.get_files_for_queued_jobs(input_file_ids):
                input_files[input_file.id] = input_file

        # Bulk create queue models
        queues = []
        configurator = QueuedExecutionConfigurator(input_files)
        for job in queued_jobs:
            config = configurator.configure_queued_job(job)

            manifest = None
            if JobInterfaceSunset.is_seed_dict(job.job_type.manifest):
                manifest = SeedManifest(job.job_type.manifest)

            if priority:
                queued_priority = priority
            elif job.priority:
                queued_priority = job.priority
            elif job.batch and self.batch.get_configuration().priority:
                queued_priority = self.batch.get_configuration().priority
            else:
                queued_priority = job.job_type.get_job_configuration().priority

            queue = Queue()
            # select_related from get_jobs_with_related above will only make a single query
            queue.docker_image = job.job_type_rev.docker_image
            queue.job_type_id = job.job_type_id
            queue.job_id = job.id
            queue.recipe_id = job.recipe_id
            queue.batch_id = job.batch_id
            queue.exe_num = job.num_exes
            queue.input_file_size = job.input_file_size if job.input_file_size else 0.0
            queue.is_canceled = False
            queue.priority = queued_priority
            queue.timeout = manifest.get_timeout() if manifest else job.timeout
            queue.interface = job.get_job_interface().get_dict()
            queue.configuration = config.get_dict()
            queue.resources = job.get_resources().get_json().get_dict()
            queue.queued = when_queued
            queues.append(queue)

        if queues:
            self.bulk_create(queues)

        return queued_job_ids

    # TODO: remove once REST API v5 is removed
    @transaction.atomic
    def handle_job_cancellation(self, job_id, when):
        """Handles the cancellation of a job. All database changes occur in an atomic transaction.

        :param job_id: The ID of the job to be canceled
        :type job_id: int
        :param when: When the job was canceled
        :type when: :class:`datetime.datetime`
        """

        Job.objects.update_jobs_to_canceled_old([job_id], when)

        self.cancel_queued_jobs([job_id])

        # If this job is in a recipe, update dependent jobs so that they are BLOCKED
        handler = Recipe.objects.get_recipe_handler_for_job(job_id)
        if handler:
            jobs_to_blocked = handler.get_blocked_jobs()
            Job.objects.update_status(jobs_to_blocked, 'BLOCKED', when)

    @transaction.atomic
    def queue_new_job(self, job_type, data, event):
        """Creates a new job for the given type and data. The new job is immediately placed on the queue. The new job,
        job_exe, and queue models are saved in the database in an atomic transaction.

        :param job_type: The type of the new job to create and queue
        :type job_type: :class:`job.models.JobType`
        :param data: The job data to run on
        :type data: :class:`job.configuration.data.job_data.JobData`
        :param event: The event that triggered the creation of this job
        :type event: :class:`trigger.models.TriggerEvent`
        :returns: The new queued job
        :rtype: :class:`job.models.Job`

        :raises job.configuration.data.exceptions.InvalidData: If the job data is invalid
        """

        job = Job.objects.create_job_old(job_type, event.id)
        job.save()

        # No lock needed for this job since it doesn't exist outside this transaction yet
        Job.objects.populate_job_data_v5(job, data)
        self.queue_jobs([job])
        job = Job.objects.get(id=job.id)

        return job

    def queue_new_job_v6(self, job_type, data, event):
        """Creates a new job for the given type and data. The new job is immediately placed on the queue. The new job,
        job_exe, and queue models are saved in the database in an atomic transaction.

        :param job_type: The type of the new job to create and queue
        :type job_type: :class:`job.models.JobType`
        :param data: The job data to run on
        :type data: :class:`data.data.data.data`
        :param event: The event that triggered the creation of this job
        :type event: :class:`trigger.models.TriggerEvent`
        :returns: The new queued job
        :rtype: :class:`job.models.Job`

        :raises job.configuration.data.exceptions.InvalidData: If the job data is invalid
        """

        try:
            job_type_rev = JobTypeRevision.objects.get_revision(job_type.name, job_type.version, job_type.revision_num)
            with transaction.atomic():
                job = Job.objects.create_job_v6(job_type_rev, event.id, data)
                job.save()
                CommandMessageManager().send_messages([create_process_job_input_messages([job.pk])])
        except InvalidData as ex:
            raise BadParameter(unicode(ex))


        # No lock needed for this job since it doesn't exist outside this transaction yet
        self.queue_jobs([job])
        job = Job.objects.get_details(job.id)
        Job.objects.process_job_input(job)

        return job

    # TODO: once Django user auth is used, have the user information passed into here
    @transaction.atomic
    def queue_new_job_for_user_v6(self, job_type, job_data, job_configuration=None):
        """Creates a new job for the given type and data at the request of a user. The new job is immediately placed on
        the queue. The given job_type model must have already been saved in the database (it must have an ID). The new
        job, event, job_exe, and queue models are saved in the database in an atomic transaction. If the data is
        invalid, a :class:`job.configuration.data.exceptions.InvalidData` will be thrown.

        :param job_type: The type of the new job to create and queue
        :type job_type: :class:`job.models.JobType`
        :param job_data: JSON description defining the job data to run on
        :type job_data: data.data.data.data
        :returns: The ID of the new job
        :rtype: int
        """

        description = {'user': 'Anonymous'}
        event = TriggerEvent.objects.create_trigger_event('USER', None, description, timezone.now())

        job_id = self.queue_new_job_v6(job_type, job_data, event).id
        return job_id

    def queue_new_job_for_user(self, job_type, data):
        """Creates a new job for the given type and data at the request of a user. The new job is immediately placed on
        the queue. The given job_type model must have already been saved in the database (it must have an ID). The new
        job, event, job_exe, and queue models are saved in the database in an atomic transaction. If the data is
        invalid, a :class:`job.configuration.data.exceptions.InvalidData` will be thrown.

        :param job_type: The type of the new job to create and queue
        :type job_type: :class:`job.models.JobType`
        :param data: JSON description defining the job data to run on
        :type data: dict
        :returns: The ID of the new job
        :rtype: int
        """

        description = {'user': 'Anonymous'}
        event = TriggerEvent.objects.create_trigger_event('USER', None, description, timezone.now())

        # TODO: Remove old JobData in v6 when we transition to only Seed job types
        if 'version' in data and '6' == data['version']:
            job_data = JobData(data)
        else:
            job_data = JobData_1_0(data)

        job_id = self.queue_new_job(job_type, job_data, event).id
        return job_id

    @transaction.atomic
    def queue_new_recipe(self, recipe_type, data, event, batch_id=None, superseded_recipe=None, delta=None,
                         superseded_jobs=None, priority=None):
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
        :param batch_id: The ID of the batch that contains this recipe
        :type batch_id: int
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
        handler = Recipe.objects.create_recipe_old(recipe_type, data, event, batch_id, superseded_recipe, delta,
                                                   superseded_jobs, priority)
        jobs_to_queue = []
        for job_tuple in handler.get_existing_jobs_to_queue():
            job = job_tuple[0]
            job_data = job_tuple[1]
            try:
                Job.objects.populate_job_data_v5(job, job_data)
            except InvalidData as ex:
                raise Exception('Scale created invalid job data: %s' % str(ex))
            jobs_to_queue.append(job)
        if jobs_to_queue:
            self.queue_jobs(jobs_to_queue)

        return handler

    def queue_new_recipe_v6(self, recipe_type, recipe_input, event, recipe_config=None, batch_id=None, superseded_recipe=None):
        """Creates a new recipe for the given type and data. and queues any of its jobs that are ready to run. If the
        new recipe is superseding an old recipe, superseded_recipe, delta, and superseded_jobs must be provided and the
        caller must have obtained a model lock on all job models in superseded_jobs and on the superseded_recipe model.
        All database changes occur in an atomic transaction.

        :param recipe_type: The type of the new recipe to create
        :type recipe_type: :class:`recipe.models.RecipeType`
        :param recipe_input: The recipe data to run on, should be None if superseded_recipe is provided
        :type recipe_input: :class:`data.data.data.data`
        :param event: The event that triggered the creation of this recipe
        :type event: :class:`trigger.models.TriggerEvent`
        :param recipe_config: config of the recipe
        :param batch_id: The ID of the batch that contains this recipe
        :type batch_id: int
        :param superseded_recipe: The recipe that the created recipe is superseding, possibly None
        :type superseded_recipe: :class:`recipe.models.Recipe`
        :returns: New recipe type
        :rtype: :class:`recipe.models.Recipe`

        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeData`: If the recipe data is invalid
        """

        recipe_type_rev = RecipeTypeRevision.objects.get_revision(recipe_type.name, recipe_type.revision_num)
        with transaction.atomic():
            recipe = Recipe.objects.create_recipe_v6(recipe_type_rev, event.pk, recipe_input,None,None, batch_id=None, superseded_recipe=None )
            recipe.save()
            CommandMessageManager().send_messages(create_process_recipe_input_messages([recipe.pk]))
            Recipe.objects.process_recipe_input(recipe)
        return recipe

    # TODO: once Django user auth is used, have the user information passed into here
    @transaction.atomic
    def queue_new_recipe_for_user_v6(self, recipe_type, recipe_input, recipe_config=None):
        """Creates a new recipe for the given type and data at the request of a user.

        The new jobs in the recipe with no dependencies on other jobs are immediately placed on the queue. The given
        event model must have already been saved in the database (it must have an ID). All database changes occur in an
        atomic transaction.

        :param recipe_type: The type of the new recipe to create
        :type recipe_type: :class:`recipe.models.RecipeType`
        :param recipe_input: The recipe data to run on, should be None if superseded_recipe is provided
        :type recipe_input: :class:`data.data.data.data`
        :returns: A handler for the new recipe
        :rtype: :class:`recipe.handlers.handler.RecipeHandler`

        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeData`: If the recipe data is invalid
        """

        description = {'user': 'Anonymous'}
        event = TriggerEvent.objects.create_trigger_event('USER', None, description, timezone.now())

        return self.queue_new_recipe_v6(recipe_type, recipe_input, event, recipe_config)

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

    # TODO: remove this (and old functions used here) when REST API v5 is removed
    @transaction.atomic
    def requeue_jobs(self, job_ids, priority=None):
        """Re-queues the jobs with the given IDs. Any job that is not in a valid state for being re-queued or is
        superseded will be ignored. All database changes will occur within an atomic transaction.

        :param job_ids: The IDs of the jobs to re-queue
        :type job_ids: [int]
        :param priority: An optional argument to reset the jobs' priority before they are queued
        :type priority: int
        """

        jobs_to_requeue = Job.objects.get_locked_jobs_with_related(job_ids)
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
            Job.objects.increment_max_tries_old(jobs_to_queue)
            self.queue_jobs(jobs_to_queue, requeue=True, priority=priority)
        when = timezone.now()
        if jobs_to_blocked:
            Job.objects.update_status(jobs_to_blocked, 'BLOCKED', when)

        # Update dependent recipe jobs (with model locks) that should now go back to PENDING
        for handler in Recipe.objects.get_recipe_handlers_for_jobs(all_valid_job_ids):
            jobs_to_pending.extend(handler.get_pending_jobs())
        if jobs_to_pending:
            Job.objects.update_status(jobs_to_pending, 'PENDING', when)


class Queue(models.Model):
    """Represents a job execution that is queued and ready to be run on a node

    :keyword job_type: The type of this job
    :type job_type: :class:`django.db.models.ForeignKey`
    :keyword job: The job that has been queued
    :type job: :class:`django.db.models.ForeignKey`
    :keyword recipe: The original recipe that created this job
    :type recipe: :class:`django.db.models.ForeignKey`
    :keyword batch: The batch that contains this job
    :type batch: :class:`django.db.models.ForeignKey`
    :keyword exe_num: The number for this job execution
    :type exe_num: :class:`django.db.models.IntegerField`

    :keyword input_file_size: The amount of disk space in MiB required for input files for this job
    :type input_file_size: :class:`django.db.models.FloatField`
    :keyword is_canceled: Whether this queued job execution has been canceled
    :type is_canceled: :class:`django.db.models.BooleanField`
    :keyword priority: The priority of the job (lower number is higher priority)
    :type priority: :class:`django.db.models.IntegerField`
    :keyword timeout: The maximum amount of time to allow this execution to run before being killed (in seconds)
    :type timeout: :class:`django.db.models.IntegerField`

    :keyword interface: JSON description describing the job's interface
    :type interface: :class:`django.contrib.postgres.fields.JSONField`
    :keyword configuration: JSON description describing the execution configuration for how the job should be run
    :type configuration: :class:`django.contrib.postgres.fields.JSONField`
    :keyword resources: JSON description describing the resources required for this job
    :type resources: :class:`django.contrib.postgres.fields.JSONField`

    :keyword created: When the queue model was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword queued: When the job was placed onto the queue
    :type queued: :class:`django.db.models.DateTimeField`
    :keyword docker_image: The docker image to be retrieved for job that is retrieved from job_type_rev.docker_image
    :type docker_image: str
    """

    job_type = models.ForeignKey('job.JobType', on_delete=models.PROTECT)
    job = models.ForeignKey('job.Job', on_delete=models.PROTECT)
    recipe = models.ForeignKey('recipe.Recipe', blank=True, null=True, on_delete=models.PROTECT)
    batch = models.ForeignKey('batch.Batch', blank=True, null=True, on_delete=models.PROTECT)
    exe_num = models.IntegerField()

    input_file_size = models.FloatField()
    is_canceled = models.BooleanField(default=False)
    priority = models.IntegerField(db_index=True)
    timeout = models.IntegerField()

    interface = django.contrib.postgres.fields.JSONField(default=dict)
    configuration = django.contrib.postgres.fields.JSONField(default=dict)
    resources = django.contrib.postgres.fields.JSONField(default=dict)

    created = models.DateTimeField(auto_now_add=True)
    queued = models.DateTimeField()

    docker_image = models.TextField(default='')

    objects = QueueManager()

    def get_execution_configuration(self):
        """Returns the execution configuration for this queued job

        :returns: The execution configuration for this queued job
        :rtype: :class:`job.execution.configuration.json.exe_config.ExecutionConfiguration`
        """

        return ExecutionConfiguration(self.configuration, do_validate=False)

    def get_job_interface(self):
        """Returns the interface for this queued job

        :returns: The job interface
        :rtype: :class:`job.configuration.interface.job_interface.JobInterface`
        """

        return JobInterfaceSunset.create(self.interface, do_validate=False)

    def get_resources(self):
        """Returns the resources required by this queued job

        :returns: The required resources
        :rtype: :class:`node.resources.node_resources.NodeResources`
        """

        return Resources(self.resources, do_validate=False).get_node_resources()

    class Meta(object):
        """meta information for the db"""
        db_table = 'queue'
