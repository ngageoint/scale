"""Defines the database models for jobs and job types"""
from __future__ import unicode_literals

import copy
import datetime
import logging
import math
import urllib

import django.utils.timezone as timezone
import djorm_pgjson.fields
from django.db import models, transaction
from django.db.models import Q

from error.models import Error
from job.configuration.data.job_data import JobData
from job.configuration.environment.job_environment import JobEnvironment
from job.configuration.interface.error_interface import ErrorInterface
from job.configuration.interface.job_interface import JobInterface
from job.configuration.results.job_results import JobResults
from job.exceptions import InvalidJobField
from job.triggers.configuration.trigger_rule import JobTriggerRuleConfiguration
from storage.models import ScaleFile
from trigger.configuration.exceptions import InvalidTriggerType
from trigger.models import TriggerRule
from util.exceptions import RollbackTransaction


logger = logging.getLogger(__name__)


# Required resource minimums for jobs (e.g. resources required for pre and post tasks)
MIN_CPUS = 0.25
MIN_MEM = 128.0
MIN_DISK = 0.0


# IMPORTANT NOTE: Locking order
# Always adhere to the following model order for obtaining row locks via select_for_update() in order to prevent
# deadlocks and ensure query efficiency
# When applying status updates to jobs: JobExecution, Queue, Job, Recipe
# When editing a job/recipe type: RecipeType, JobType, TriggerRule


class JobManager(models.Manager):
    """Provides additional methods for handling jobs
    """

    def complete_job(self, job, when, results):
        """Updates the given job to COMPLETED status. The caller must have obtained a model lock on the job model.

        :param job: The job to update
        :type job: :class:`job.models.Job`
        :param when: The time that the job was completed
        :type when: :class:`datetime.datetime`
        :param results: The error that caused the failure (required if status is FAILED, should be None otherwise)
        :type results: :class:`job.configuration.results.job_results.JobResults`
        """

        job.status = 'COMPLETED'
        job.results = results.get_dict()
        job.ended = when
        job.last_status_change = when
        job.save()

    def create_job(self, job_type, event, superseded_job=None, delete_superseded=True):
        """Creates a new job for the given type and returns the job model. Optionally a job can be provided that the new
        job is superseding. If provided, the caller must have obtained a model lock on the job to supersede. The
        returned job model will have not yet been saved in the database.

        :param job_type: The type of the job to create
        :type job_type: :class:`job.models.JobType`
        :param event: The event that triggered the creation of this job
        :type event: :class:`trigger.models.TriggerEvent`
        :param superseded_job: The job that the created job is superseding, possibly None
        :type superseded_job: :class:`job.models.Job`
        :param delete_superseded: Whether the created job should delete products from the superseded job
        :type delete_superseded: :class:`job.models.Job`
        :returns: The new job
        :rtype: :class:`job.models.Job`
        """

        if not job_type.is_active:
            raise Exception('Job type is no longer active')
        if event is None:
            raise Exception('Event that triggered job creation is required')

        job = Job()
        job.job_type = job_type
        job.job_type_rev = JobTypeRevision.objects.get_revision(job_type.id, job_type.revision_num)
        job.event = event
        job.priority = job_type.priority
        job.timeout = job_type.timeout
        job.docker_params = job_type.docker_params
        job.max_tries = job_type.max_tries
        job.cpus_required = max(job_type.cpus_required, MIN_CPUS)
        job.mem_required = max(job_type.mem_required, MIN_MEM)

        if superseded_job:
            root_id = superseded_job.root_superseded_job_id
            if not root_id:
                root_id = superseded_job.id
            job.root_superseded_job_id = root_id
            job.superseded_job = superseded_job
            job.delete_superseded = delete_superseded

        return job

    def get_jobs(self, started=None, ended=None, status=None, job_ids=None, job_type_ids=None, job_type_names=None,
                 job_type_categories=None, order=None):
        """Returns a list of jobs within the given time range.

        :param started: Query jobs updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query jobs updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param status: Query jobs with the a specific execution status.
        :type status: str
        :param job_ids: Query jobs associated with the identifier.
        :type job_ids: list[int]
        :param job_type_ids: Query jobs of the type associated with the identifier.
        :type job_type_ids: list[int]
        :param job_type_names: Query jobs of the type associated with the name.
        :type job_type_names: list[str]
        :param job_type_categories: Query jobs of the type associated with the category.
        :type job_type_categories: list[str]
        :param order: A list of fields to control the sort order.
        :type order: list[str]
        :returns: The list of jobs that match the time range.
        :rtype: list[:class:`job.models.Job`]
        """

        # Fetch a list of jobs
        jobs = Job.objects.all().select_related('job_type', 'job_type_rev', 'event', 'error')
        jobs = jobs.defer('job_type__interface', 'job_type_rev__job_type', 'job_type_rev__interface')

        # Apply time range filtering
        if started:
            jobs = jobs.filter(last_modified__gte=started)
        if ended:
            jobs = jobs.filter(last_modified__lte=ended)

        if status:
            jobs = jobs.filter(status=status)
        if job_ids:
            jobs = jobs.filter(id__in=job_ids)
        if job_type_ids:
            jobs = jobs.filter(job_type_id__in=job_type_ids)
        if job_type_names:
            jobs = jobs.filter(job_type__name__in=job_type_names)
        if job_type_categories:
            jobs = jobs.filter(job_type__category__in=job_type_categories)

        # Apply sorting
        if order:
            jobs = jobs.order_by(*order)
        else:
            jobs = jobs.order_by('last_modified')
        return jobs

    def get_details(self, job_id):
        """Gets additional details for the given job model based on related model attributes.

        The additional fields include: input files, recipe, job executions, and generated products.

        :param job_id: The unique identifier of the job.
        :type job_id: int
        :returns: The job with extra related attributes.
        :rtype: :class:`job.models.Job`
        """

        # Attempt to fetch the requested job
        job = Job.objects.select_related('job_type', 'job_type_rev', 'event', 'event__rule', 'error').get(pk=job_id)

        # Attempt to get related job executions
        job.job_exes = JobExecution.objects.filter(job=job).order_by('-created')

        # Attempt to get related recipe
        # Use a localized import to make higher level application dependencies optional
        try:
            from recipe.models import RecipeJob
            recipe_jobs = RecipeJob.objects.filter(job=job).order_by('recipe__last_modified')
            recipe_jobs = recipe_jobs.select_related('recipe', 'recipe__recipe_type')
            job.recipes = [recipe_job.recipe for recipe_job in recipe_jobs]
        except:
            job.recipes = []

        # Fetch all the associated input files
        input_file_ids = job.get_job_data().get_input_file_ids()
        input_files = ScaleFile.objects.filter(id__in=input_file_ids)
        input_files = input_files.select_related('workspace').defer('workspace__json_config')
        input_files = input_files.order_by('id').distinct('id')

        # Attempt to get related products
        # Use a localized import to make higher level application dependencies optional
        try:
            from product.models import ProductFile
            output_files = ProductFile.objects.filter(job=job)
            output_files = output_files.select_related('file', 'file__workspace').defer('file__workspace__json_config')
            output_files = output_files.order_by('id').distinct('id')
        except:
            output_files = []

        # Merge job interface definitions with mapped values
        job_interface_dict = job.get_job_interface().get_dict()
        job.inputs = self._merge_job_data(job_interface_dict['input_data'],
                                          job.get_job_data().get_dict()['input_data'], input_files)
        job.outputs = self._merge_job_data(job_interface_dict['output_data'],
                                           job.get_job_results().get_dict()['output_data'], output_files)

        # TODO Remove these attributes once the UI migrates to "inputs" and "outputs"
        job.input_files = input_files
        job.products = output_files
        return job

    def get_job_updates(self, started=None, ended=None, status=None, job_type_ids=None,
                        job_type_names=None, job_type_categories=None, order=None):
        """Returns a list of jobs that changed status within the given time range.

        :param started: Query jobs updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query jobs updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param status: Query jobs with the a specific execution status.
        :type status: str
        :param job_type_ids: Query jobs of the type associated with the identifier.
        :type job_type_ids: list[int]
        :param job_type_categories: Query jobs of the type associated with the category.
        :type job_type_categories: list[str]
        :param job_type_names: Query jobs of the type associated with the name.
        :type job_type_names: list[str]
        :param order: A list of fields to control the sort order.
        :type order: list[str]
        :returns: The list of jobs that match the time range.
        :rtype: list[:class:`job.models.Job`]
        """
        if not order:
            order = ['last_status_change']
        return self.get_jobs(started=started, ended=ended, status=status, job_type_ids=job_type_ids,
                             job_type_names=job_type_names, job_type_categories=job_type_categories, order=order)

    def get_locked_job(self, job_id):
        """Gets the job model with the given ID with a model lock obtained and related job_type and job_type_rev models

        :param job_id: The job ID
        :type job_id: int
        :returns: The job model
        :rtype: :class:`job.models.Job`
        """

        return self.get_locked_jobs([job_id])[0]

    def get_locked_jobs(self, job_ids):
        """Gets the job models for the given IDs with model locks obtained and related job_type and job_type_rev models

        :param job_ids: The job IDs
        :type job_ids: [int]
        :returns: The job models
        :rtype: [:class:`job.models.Job`]
        """

        self.lock_jobs(job_ids)

        return list(self.select_related('job_type', 'job_type_rev').filter(id__in=job_ids).iterator())

    def increment_max_tries(self, jobs):
        """Increments the max_tries of the given jobs to be one greater than their current number of executions. The
        caller must have obtained model locks on the job models.

        :param jobs: The jobs to update
        :type jobs: [:class:`job.models.Job`]
        """

        modified = timezone.now()

        # Update job models in memory and collect job IDs
        job_ids = set()
        for job in jobs:
            job_ids.add(job.id)
            job.max_tries = job.num_exes + 1
            job.last_modified = modified

        # Update job models in database with single query
        self.filter(id__in=job_ids).update(max_tries=models.F('num_exes') + 1, last_modified=modified)

    def lock_jobs(self, job_ids):
        """Obtains model locks on the job models with the given IDs (in ID order to prevent deadlocks)

        :param job_ids: The IDs of the jobs to lock
        :type job_ids: [int]
        """

        # Dummy list is used here to force query execution
        # Unfortunately this query can't usually be combined with other queries since using select_related() with
        # select_for_update() will cause the related fields to be locked as well. This requires 2 passes, such as the
        # two queries in get_locked_jobs().
        list(self.select_for_update().filter(id__in=job_ids).order_by('id').iterator())

    def queue_jobs(self, jobs, when, priority=None):
        """Queues the given jobs and returns the new queued job executions. The caller must have obtained model locks on
        the job models. Any jobs not in a valid status for being queued or without job data will be ignored. All jobs
        should have their related job_type and job_type_rev models populated.

        :param jobs: The jobs to put on the queue
        :type jobs: [:class:`job.models.Job`]
        :param when: The time that the jobs are queued
        :type when: :class:`datetime.datetime`
        :param priority: An optional argument to reset the jobs' priority before they are queued
        :type priority: int
        :returns: The new queued job execution models
        :rtype: [:class:`job.models.JobExecution`]
        """

        modified = timezone.now()

        # Update job models in memory and collect job IDs
        job_ids = set()
        jobs_to_queue = []
        for job in jobs:
            if not job.is_ready_to_queue or not job.data:
                continue

            job_ids.add(job.id)
            jobs_to_queue.append(job)
            job.status = 'QUEUED'
            job.error = None
            job.queued = when
            job.started = None
            job.ended = None
            job.last_status_change = when
            job.num_exes += 1
            if priority:
                job.priority = priority
            job.last_modified = modified

        # Update job models in database with single query
        if priority:
            self.filter(id__in=job_ids).update(status='QUEUED', error=None, queued=when, started=None, ended=None,
                                               last_status_change=when, num_exes=models.F('num_exes') + 1,
                                               priority=priority, last_modified=modified)
        else:
            self.filter(id__in=job_ids).update(status='QUEUED', error=None, queued=when, started=None, ended=None,
                                               last_status_change=when, num_exes=models.F('num_exes') + 1,
                                               last_modified=modified)

        return JobExecution.objects.queue_job_exes(jobs_to_queue, when)

    def populate_job_data(self, job, data):
        """Populates the job data and all derived fields for the given job. The caller must have obtained a model lock
        on the job model. The job should have its related job_type and job_type_rev models populated.

        :param job: The job
        :type job: :class:`job.models.Job`
        :param data: JSON description defining the job data to run on
        :type data: :class:`job.configuration.data.job_data.JobData`
        :raises job.configuration.data.exceptions.InvalidData: If the job data is invalid
        """

        modified = timezone.now()

        # Validate job data
        interface = job.get_job_interface()
        interface.validate_data(data)

        # Calculate disk space required for the job
        input_file_ids = data.get_input_file_ids()
        # Get total input file size in MiB rounded up to the nearest whole MiB
        input_size_mb = long(math.ceil((ScaleFile.objects.get_total_file_size(input_file_ids) / (1024.0 * 1024.0))))
        # Calculate output space required in MiB rounded up to the nearest whole MiB
        multiplier = job.job_type.disk_out_mult_required
        const = job.job_type.disk_out_const_required
        output_size_mb = long(math.ceil(multiplier * input_size_mb + const))
        disk_in_required = max(input_size_mb, MIN_DISK)
        disk_out_required = max(output_size_mb, MIN_DISK)

        # Update job model in memory
        job.data = data.get_dict()
        job.disk_in_required = disk_in_required
        job.disk_out_required = disk_out_required
        job.last_modified = modified

        # Update job model in database with single query
        self.filter(id=job.id).update(data=data.get_dict(), disk_in_required=disk_in_required,
                                      disk_out_required=disk_out_required, last_modified=modified)

    def populate_input_files(self, jobs):
        """Populates each of the given jobs with its input file references in a field called "input_files".

        :param jobs: The list of jobs to augment with input files.
        :type jobs: list[:class:`job.models.Job`]
        """

        # Build a unique set of all input file identifiers
        # Build a mapping of job to its input file identifiers
        file_ids = set()
        job_file_map = dict()
        for job in jobs:
            input_file_ids = job.get_job_data().get_input_file_ids()
            job_file_map[job.id] = input_file_ids
            file_ids.update(input_file_ids)
            job.input_files = []

        # Fetch all the required source files
        input_files = ScaleFile.objects.filter(id__in=file_ids)
        input_files = input_files.select_related('workspace').defer('workspace__json_config')
        input_files = input_files.order_by('id').distinct('id')

        # Build a mapping of input file identifiers to input file
        input_file_map = {input_file.id: input_file for input_file in input_files}

        # Update each job with source file models
        for job in jobs:
            input_file_ids = job_file_map[job.id]
            for input_file_id in input_file_ids:
                if input_file_id in input_file_map:
                    job.input_files.append(input_file_map[input_file_id])

    def supersede_jobs(self, jobs, when):
        """Updates the given jobs to be superseded. The caller must have obtained model locks on the job models.

        :param jobs: The jobs to supersede
        :type jobs: [:class:`job.models.Job`]
        :param when: The time that the jobs were superseded
        :type when: :class:`datetime.datetime`
        """

        modified = timezone.now()

        # Update job models in memory and collect job IDs
        job_ids = set()
        for job in jobs:
            job_ids.add(job.id)
            job.is_superseded = True
            job.superseded = when
            job.last_modified = modified

        # Update job models in database with single query
        self.filter(id__in=job_ids).update(is_superseded=True, superseded=when, last_modified=modified)

    def update_status(self, jobs, status, when, error=None):
        """Updates the given jobs with the new status. The caller must have obtained model locks on the job models.

        :param jobs: The jobs to update
        :type jobs: [:class:`job.models.Job`]
        :param status: The new status
        :type status: str
        :param when: The time that the status change occurred
        :type when: :class:`datetime.datetime`
        :param error: The error that caused the failure (required if status is FAILED, should be None otherwise)
        :type error: :class:`error.models.Error`
        """

        if status == 'QUEUED':
            raise Exception('Changing status to QUEUED must use the queue_jobs() method')
        if status == 'FAILED' and not error:
            raise Exception('An error is required when status is FAILED')
        if not status == 'FAILED' and error:
            raise Exception('Status %s is invalid with an error' % status)

        change_started = (status == 'RUNNING')
        ended = when if status in Job.FINAL_STATUSES else None
        modified = timezone.now()

        # Update job models in memory and collect job IDs
        job_ids = set()
        for job in jobs:
            job_ids.add(job.id)
            job.status = status
            job.last_status_change = when
            if change_started:
                job.started = when
            job.ended = ended
            job.error = error
            job.last_modified = modified

        # Update job models in database with single query
        if change_started:
            self.filter(id__in=job_ids).update(status=status, last_status_change=when, started=when, ended=ended,
                                               error=error, last_modified=modified)
        else:
            self.filter(id__in=job_ids).update(status=status, last_status_change=when, ended=ended, error=error,
                                               last_modified=modified)

    def _merge_job_data(self, job_interface_dict, job_data_dict, job_files):

        # Setup the basic structure for merged results
        merged_dicts = copy.deepcopy(job_interface_dict)
        name_map = {merged_dict['name']: merged_dict for merged_dict in merged_dicts}
        file_map = {job_file.id: job_file for job_file in job_files}

        # Merge the job data with the result data
        for data_dict in job_data_dict:
            value = None
            if 'value' in data_dict:
                value = data_dict['value']
            elif 'file_id' in data_dict:
                value = file_map[data_dict['file_id']]
            elif 'file_ids' in data_dict:
                value = [file_map[file_id] for file_id in data_dict['file_ids']]

            merged_dict = name_map[data_dict['name']]
            merged_dict['value'] = value
        return merged_dicts


class Job(models.Model):
    """Represents a job to be run on the cluster. Any status updates to a job model requires obtaining a lock on the
    model using select_for_update(). If a related job execution model is changing status as well, its model lock must be
    obtained BEFORE obtaining the lock for the job model.

    :keyword job_type: The type of this job
    :type job_type: :class:`django.db.models.ForeignKey`
    :keyword job_type_rev: The revision of the job type when this job was created
    :type job_type_rev: :class:`django.db.models.ForeignKey`
    :keyword status: The status of the job
    :type status: :class:`django.db.models.CharField`
    :keyword event: The event that triggered the creation of this job
    :type event: :class:`django.db.models.ForeignKey`
    :keyword error: The error that caused the failure (should only be set when status is FAILED)
    :type error: :class:`django.db.models.ForeignKey`

    :keyword data: JSON description defining the data for this job. This field must be populated when the job is first
        queued.
    :type data: :class:`djorm_pgjson.fields.JSONField`
    :keyword results: JSON description defining the results for this job. This field is populated when the job is
        successfully completed.
    :type results: :class:`djorm_pgjson.fields.JSONField`
    :keyword docker_params: JSON array of 2-tuples (key-value) which will be passed as-is to docker.
    See the mesos prototype file for further information.
    :type docker_params: :class:`djorm_pgjson.fields.JSONField`

    :keyword priority: The priority of the job (lower number is higher priority)
    :type priority: :class:`django.db.models.IntegerField`
    :keyword timeout: The maximum amount of time to allow this job to run before being killed (in seconds)
    :type timeout: :class:`django.db.models.IntegerField`
    :keyword max_tries: The maximum number of times to try executing this job in case of errors (minimum one)
    :type max_tries: :class:`django.db.models.IntegerField`
    :keyword num_exes: The number of executions this job has had
    :type num_exes: :class:`django.db.models.IntegerField`
    :keyword cpus_required: The number of CPUs required for this job
    :type cpus_required: :class:`django.db.models.FloatField`
    :keyword mem_required: The amount of RAM in MiB required for this job
    :type mem_required: :class:`django.db.models.FloatField`
    :keyword disk_in_required: The amount of disk space in MiB required for input files for this job
    :type disk_in_required: :class:`django.db.models.FloatField`
    :keyword disk_out_required: The amount of disk space in MiB required for output (temp work and products) for this
        job
    :type disk_out_required: :class:`django.db.models.FloatField`

    :keyword is_superseded: Whether this job has been superseded and is obsolete. This may be true while
        superseded_by_job (the reverse relationship of superded_job) is null, indicating that this job is obsolete (its
        recipe has been superseded), but there is no new job that has directly taken its place.
    :type is_superseded: :class:`django.db.models.BooleanField`
    :keyword root_superseded_job: The first job in the chain of superseded jobs. This field will be null for the first
        job in the chain (i.e. jobs that have a null superseded_job field).
    :type root_superseded_job: :class:`django.db.models.ForeignKey`
    :keyword superseded_job: The job that was directly superseded by this job. The reverse relationship can be accessed
        using 'superseded_by_job'.
    :type superseded_job: :class:`django.db.models.ForeignKey`
    :keyword delete_superseded: Whether this job should delete the products of the job that it has directly superseded
    :type delete_superseded: :class:`django.db.models.BooleanField`

    :keyword created: When the job was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword queued: When the job was added to the queue to be run when resources are available
    :type queued: :class:`django.db.models.DateTimeField`
    :keyword started: When the job started running
    :type started: :class:`django.db.models.DateTimeField`
    :keyword ended: When the job stopped running, which could be due to successful completion or an error condition
    :type ended: :class:`django.db.models.DateTimeField`
    :keyword last_status_change: When the job's last status change occurred
    :type last_status_change: :class:`django.db.models.DateTimeField`
    :keyword superseded: When this job was superseded
    :type superseded: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the job was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`
    """
    JOB_STATUSES = (
        ('PENDING', 'PENDING'),
        ('BLOCKED', 'BLOCKED'),
        ('QUEUED', 'QUEUED'),
        ('RUNNING', 'RUNNING'),
        ('FAILED', 'FAILED'),
        ('COMPLETED', 'COMPLETED'),
        ('CANCELED', 'CANCELED'),
    )
    FINAL_STATUSES = ['FAILED', 'COMPLETED', 'CANCELED']

    job_type = models.ForeignKey('job.JobType', on_delete=models.PROTECT)
    job_type_rev = models.ForeignKey('job.JobTypeRevision', on_delete=models.PROTECT)
    status = models.CharField(choices=JOB_STATUSES, default='PENDING', max_length=50, db_index=True)
    event = models.ForeignKey('trigger.TriggerEvent', on_delete=models.PROTECT)
    error = models.ForeignKey('error.Error', blank=True, null=True, on_delete=models.PROTECT)

    data = djorm_pgjson.fields.JSONField()
    results = djorm_pgjson.fields.JSONField()
    docker_params = djorm_pgjson.fields.JSONField(null=True)

    priority = models.IntegerField()
    timeout = models.IntegerField()
    max_tries = models.IntegerField()
    num_exes = models.IntegerField(default=0)
    cpus_required = models.FloatField(blank=True, null=True)
    mem_required = models.FloatField(blank=True, null=True)
    disk_in_required = models.FloatField(blank=True, null=True)
    disk_out_required = models.FloatField(blank=True, null=True)

    is_superseded = models.BooleanField(default=False)
    root_superseded_job = models.ForeignKey('job.Job', related_name='superseded_by_jobs', blank=True, null=True, on_delete=models.PROTECT)
    superseded_job = models.OneToOneField('job.Job', related_name='superseded_by_job', blank=True, null=True, on_delete=models.PROTECT)
    delete_superseded = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    queued = models.DateTimeField(blank=True, null=True)
    started = models.DateTimeField(blank=True, null=True)
    ended = models.DateTimeField(blank=True, null=True)
    last_status_change = models.DateTimeField(blank=True, null=True)
    superseded = models.DateTimeField(blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = JobManager()

    def get_job_data(self):
        """Returns the data for this job

        :returns: The data for this job
        :rtype: :class:`job.configuration.data.job_data.JobData`
        """

        return JobData(self.data)

    def get_job_interface(self):
        """Returns the interface for this job

        :returns: The interface for this job
        :rtype: :class:`job.configuration.interface.job_interface.JobInterface`
        """

        return JobInterface(self.job_type_rev.interface)

    def get_job_results(self):
        """Returns the results for this job

        :returns: The results for this job
        :rtype: :class:`job.configuration.results.job_results.JobResults`
        """

        return JobResults(self.results)

    def increase_max_tries(self):
        """Increase the total max_tries based on the current number of executions and job type max_tries.
        Callers must save the model to persist the change.
        """

        self.max_tries = self.num_exes + self.job_type.max_tries

    def _can_be_canceled(self):
        """Indicates whether this job can be canceled.

        :returns: True if the job status allows the job to be canceled, false otherwise.
        :rtype: bool
        """

        return self.status not in ['COMPLETED', 'CANCELED']
    can_be_canceled = property(_can_be_canceled)

    def _is_ready_to_queue(self):
        """Indicates whether this job can be added to the queue.

        :returns: True if the job status allows the job to be queued, false otherwise.
        :rtype: bool
        """

        return self.status in ['PENDING', 'CANCELED', 'FAILED']
    is_ready_to_queue = property(_is_ready_to_queue)

    def _is_ready_to_requeue(self):
        """Indicates whether this job can be added to the queue after being attempted previously.

        :returns: True if the job status allows the job to be queued, false otherwise.
        :rtype: bool
        """

        return self.status in ['CANCELED', 'FAILED']
    is_ready_to_requeue = property(_is_ready_to_requeue)

    class Meta(object):
        """meta information for the db"""
        db_table = 'job'
        index_together = ['last_modified', 'job_type', 'status']


class JobExecutionManager(models.Manager):
    """Provides additional methods for handling job executions."""

    def cleanup_completed(self, job_exe_id, when):
        """Updates the given job execution to reflect that its cleanup has completed successfully

        :param job_exe_id: The job execution that was cleaned up
        :type job_exe_id: int
        :param when: The time that the cleanup was completed
        :type when: :class:`datetime.datetime`
        """

        modified = timezone.now()
        self.filter(id=job_exe_id).update(requires_cleanup=False, cleaned_up=when, last_modified=modified)

    def complete_job_exe(self, job_exe, when):
        """Updates the given job execution and its job to COMPLETED. The caller must have obtained model locks on the
        job execution and job models (in that order).

        :param job_exe: The job execution (with related job model) to complete
        :type job_exe: :class:`job.models.JobExecution`
        :param when: The time that the job execution was completed
        :type when: :class:`datetime.datetime`
        """

        job_exe.status = 'COMPLETED'
        job_exe.ended = when
        job_exe.save()

        # Update job model
        Job.objects.complete_job(job_exe.job, when, JobResults(job_exe.results))

    def get_exes(self, started=None, ended=None, status=None, job_type_ids=None, job_type_names=None,
                 job_type_categories=None, node_ids=None, order=None):
        """Returns a list of jobs within the given time range.

        :param started: Query job executions updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query job executions updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param status: Query job executions with the a specific status.
        :type status: str
        :param job_type_ids: Query job executions of the type associated with the identifier.
        :type job_type_ids: list[int]
        :param job_type_names: Query job executions of the type associated with the name.
        :type job_type_names: list[str]
        :param job_type_categorys: Query job executions of the type associated with the category.
        :type job_type_categorys: list[str]
        :param node_ids: Query job executions that ran on a node with the identifier.
        :type node_ids: list[int]
        :param order: A list of fields to control the sort order.
        :type order: list[str]
        :returns: The list of job executions that match the time range.
        :rtype: list[:class:`job.models.JobExecution`]
        """

        # Fetch a list of job executions
        job_exes = JobExecution.objects.all().select_related('job', 'job__job_type', 'node', 'error')
        job_exes = job_exes.defer('stdout', 'stderr')

        # Apply time range filtering
        if started:
            job_exes = job_exes.filter(last_modified__gte=started)
        if ended:
            job_exes = job_exes.filter(last_modified__lte=ended)

        if status:
            job_exes = job_exes.filter(status=status)
        if job_type_ids:
            job_exes = job_exes.filter(job__job_type_id__in=job_type_ids)
        if job_type_names:
            job_exes = job_exes.filter(job__job_type__name__in=job_type_names)
        if job_type_categories:
            job_exes = job_exes.filter(job__job_type__category__in=job_type_categories)
        if node_ids:
            job_exes = job_exes.filter(node_id__in=node_ids)

        # Apply sorting
        if order:
            job_exes = job_exes.order_by(*order)
        else:
            job_exes = job_exes.order_by('last_modified')
        return job_exes

    def get_details(self, job_exe_id):
        """Gets additional details for the given job execution model based on related model attributes.

        :param job_exe_id: The unique identifier of the job execution.
        :type job_exe_id: int
        :returns: The job execution with extra related attributes.
        :rtype: :class:`job.models.JobExecution`
        """
        job_exe = JobExecution.objects.all().select_related(
            'job', 'job__job_type', 'job__error', 'job__event', 'job__event__rule', 'node', 'error'
        )
        job_exe = job_exe.defer('stdout', 'stderr')
        job_exe = job_exe.get(pk=job_exe_id)
        return job_exe

    def get_locked_job_exe(self, job_exe_id):
        """Returns the job execution with the given ID with a model lock obtained

        :param job_exe_id: The job execution ID
        :type job_exe_id: int
        :returns: The job execution model with a model lock
        :rtype: :class:`job.models.JobExecution`
        """

        return self.select_for_update().defer('stdout', 'stderr').get(pk=job_exe_id)

    def get_logs(self, job_exe_id):
        """Gets additional details for the given job execution model based on related model attributes.

        :param job_exe_id: The unique identifier of the job execution.
        :type job_exe_id: int
        :returns: The job execution with extra related attributes.
        :rtype: :class:`job.models.JobExecution`
        """
        job_exe = JobExecution.objects.all().select_related('job', 'job__job_type', 'node', 'error')
        job_exe = job_exe.get(pk=job_exe_id)

        # Add the standard output log
        if job_exe.current_stdout_url:
            try:
                response = urllib.urlopen(job_exe.current_stdout_url)
                if response.code == 200:
                    job_exe.stdout = response.read()
                else:
                    logger.error('Received invalid standard output log response: %i -> %s -> %i', job_exe.id,
                                 job_exe.current_stdout_url, response.code)
            except:
                logger.exception('Unable to fetch job execution standard output log: %i -> %s', job_exe.id,
                                 job_exe.current_stdout_url)

        # Add the standard error log
        if job_exe.current_stderr_url:
            try:
                response = urllib.urlopen(job_exe.current_stderr_url)
                if response.code == 200:
                    job_exe.stderr = response.read()
                else:
                    logger.error('Received invalid standard error log response: %i -> %s -> %i', job_exe.id,
                                 job_exe.current_stderr_url, response.code)
            except:
                logger.exception('Unable to fetch job execution standard error log: %i -> %s', job_exe.id,
                                 job_exe.current_stderr_url)

        return job_exe

    def get_job_exe_with_job_and_job_type(self, job_exe_id):
        """Gets a job execution with its related job and job_type models populated using only one database query

        :param job_exe_id: The ID of the job execution to retrieve
        :type job_exe_id: int
        :returns: The job execution model with related job and job_type models populated
        :rtype: :class:`job.models.JobExecution`
        """

        return self.select_related('job__job_type', 'job__job_type_rev').defer('stdout', 'stderr').get(pk=job_exe_id)

    def get_latest(self, jobs):
        """Gets the latest job execution associated with each given job.

        :param jobs: The jobs to populate with latest execution models.
        :type jobs: list[class:`job.models.Job`]
        :returns: A dictionary that maps each job identifier to its latest execution.
        :rtype: dict of int -> class:`job.models.JobExecution`
        """
        job_exes = JobExecution.objects.filter(job__in=jobs).defer('stdout', 'stderr')

        results = {}
        for job_exe in job_exes:
            if job_exe.job_id not in results or job_exe.created > results[job_exe.job_id].created:
                results[job_exe.job_id] = job_exe

        return results

    def get_running_job_exes(self):
        """Returns all job executions that are currently RUNNING on a node

        :returns: The list of RUNNING job executions
        :rtype: list of :class:`job.models.JobExecution`
        """

        job_exe_qry = JobExecution.objects.defer('stdout', 'stderr')
        return job_exe_qry.filter(status='RUNNING')

    def post_steps_results(self, job_exe_id, results, results_manifest):
        """Updates the given job execution to reflect that the post-job steps have finished calculating the results

        :param job_exe_id: The job execution whose results have been processed
        :type job_exe_id: int
        :param results: The job execution results
        :type results: :class:`job.configuration.results.job_results.JobResults`
        :param results_manifest: The results manifest generated by the job execution
        :type results_manifest: :class:`job.configuration.results.results_manifest.results_manifest.ResultsManifest`
        """

        if not results or not results_manifest:
            raise Exception('Job execution results and results manifest are required')

        modified = timezone.now()
        self.filter(id=job_exe_id).update(results=results.get_dict(), results_manifest=results_manifest.get_json_dict(),
                                          last_modified=modified)

    def pre_steps_command_arguments(self, job_exe_id, command_arguments):
        """Updates the given job execution after the job command argument string has been filled out.

        This typically includes pre-job step information (e.g. location of file paths).

        :param job_exe_id: The job execution whose pre-job steps have filled out the job command
        :type job_exe_id: int
        :param command_arguments: The new job execution command argument string with pre-job step information filled in
        :type command_arguments: str
        """

        modified = timezone.now()
        self.filter(id=job_exe_id).update(command_arguments=command_arguments, last_modified=modified)

    def queue_job_exes(self, jobs, when):
        """Creates, saves, and returns new job executions for the given queued jobs. The caller must have obtained model
        locks on the job models. Any jobs that are not queued will be ignored. All jobs should have their related
        job_type and job_type_rev models populated.

        :param jobs: The queued jobs
        :type jobs: [:class:`job.models.Job`]
        :param when: The time that the jobs are queued
        :type when: :class:`datetime.datetime`
        :returns: The new queued job execution models
        :rtype: [:class:`job.models.JobExecution`]
        """

        job_ids = set()
        job_exes = []
        for job in jobs:
            if job.status != 'QUEUED':
                continue

            job_ids.add(job.id)
            job_exe = JobExecution()
            job_exe.job = job
            job_exe.timeout = job.timeout
            job_exe.docker_params = job.docker_params
            job_exe.queued = when
            job_exe.created = when
            # Fill in job execution command argument string with data that doesn't require pre-task
            interface = job.get_job_interface()
            data = job.get_job_data()
            job_exe.command_arguments = interface.populate_command_argument_properties(data)
            job_exes.append(job_exe)

        # Create job executions and re-query to get ID fields
        self.bulk_create(job_exes)
        return list(self.filter(job_id__in=job_ids, status='QUEUED').iterator())

    @transaction.atomic
    def schedule_job_executions(self, job_executions):
        """Schedules the given job executions. The caller must have obtained a model lock on the given job_exe models.
        Any job_exe models that are not in the QUEUED status will be ignored. All of the job_exe and job model changes
        will be saved in the database in an atomic transaction. The updated job_exe models are returned with their
        related job, job_type, job_type_rev and node models populated.

        :param job_executions: A list of tuples where each tuple contains the job_exe model to schedule, the node to
            schedule it on, and the resources it will be given
        :type job_executions: list[(:class:`job.models.JobExecution`, :class:`node.models.Node`,
            :class:`job.resources.JobResources`)]
        :returns: The scheduled job_exe models with related job, job_type, job_type_rev and node models populated
        :rtype: list[:class:`job.models.JobExecution`]
        """

        started = timezone.now()
        job_ids = []
        for job_execution in job_executions:
            job_exe = job_execution[0]
            if job_exe.status == 'QUEUED':
                job_ids.append(job_exe.job_id)

        # Lock corresponding jobs and update them to RUNNING
        jobs = {}
        locked_jobs = Job.objects.get_locked_jobs(job_ids)
        Job.objects.update_status(locked_jobs, 'RUNNING', started)
        for job in locked_jobs:
            jobs[job.id] = job

        # Update each job execution
        job_exes = []
        for job_execution in job_executions:
            job_exe = job_execution[0]
            node = job_execution[1]
            resources = job_execution[2]

            if job_exe.status != 'QUEUED':
                continue
            if node is None:
                raise Exception('Cannot schedule job execution %i without node' % job_exe.id)
            if resources is None:
                raise Exception('Cannot schedule job execution %i without resources' % job_exe.id)
            if job_exe.status != 'QUEUED':
                msg = 'Job execution %i is %s, must be in QUEUED status to be scheduled'
                raise Exception(msg % (job_exe.id, job_exe.status))

            job_exe.job = jobs[job_exe.job_id]
            job_exe.status = 'RUNNING'
            job_exe.started = started
            job_exe.node = node
            job_exe.environment = JobEnvironment({}).get_dict()
            job_exe.cpus_scheduled = resources.cpus
            job_exe.mem_scheduled = resources.mem
            job_exe.disk_in_scheduled = resources.disk_in
            job_exe.disk_out_scheduled = resources.disk_out
            job_exe.disk_total_scheduled = resources.disk_total
            job_exe.requires_cleanup = job_exe.job.job_type.requires_cleanup
            job_exe.save()
            job_exes.append(job_exe)

        return job_exes

    # TODO: Deprecated. I don't think the task_id fields are even used. If so, they should be removed. Do so the next
    # time we make other job_exe model changes. At the same time, also rename pre_completed, job_completed, etc to
    # pre_ended, job_ended, etc. This will force changes through the REST API though, so coordinate with UI
    @transaction.atomic
    def set_task_ids(self, job_exe_id, pre_task_id, job_task_id, post_task_id):
        """Sets the task IDs for the given job execution. All database changes occur in an atomic transaction.

        :param job_exe_id: The job execution ID
        :type job_exe_id: int
        :param pre_task_id: The pre-task ID, possibly None
        :type pre_task_id: str
        :param job_task_id: The job-task ID, possibly None
        :type job_task_id: str
        :param post_task_id: The post-task ID, possibly None
        :type post_task_id: str
        """

        # Acquire model lock
        job_exe = JobExecution.objects.defer('stdout', 'stderr').select_for_update().get(pk=job_exe_id)
        job_exe.pre_task_id = pre_task_id
        job_exe.job_task_id = job_task_id
        job_exe.post_task_id = post_task_id
        job_exe.save()

    def task_ended(self, job_exe_id, task, when, exit_code, stdout, stderr):
        """Updates the given job execution to reflect that the given task has ended

        :param job_exe_id: The job execution ID
        :type job_exe_id: int
        :param task: Indicates which task, either 'pre', 'job', or 'post'
        :type task: str
        :param when: The time that the task ended
        :type when: :class:`datetime.datetime`
        :param exit_code: The task exit code, possibly None
        :type exit_code: int
        :param stdout: The task stdout contents, possibly None
        :type stdout: str
        :param stderr: The task stderr contents, possibly None
        :type stderr: str
        """

        # TODO: once we no longer have stdout and stderr in job execution model, transition this from selecting with
        # lock to using a single update query as in task_started()
        with transaction.atomic():
            # Acquire model lock
            job_exe = JobExecution.objects.select_for_update().get(pk=job_exe_id)

            if task == 'pre':
                job_exe.pre_completed = when
                job_exe.pre_exit_code = exit_code
            elif task == 'job':
                job_exe.job_completed = when
                job_exe.job_exit_code = exit_code
            elif task == 'post':
                job_exe.post_completed = when
                job_exe.post_exit_code = exit_code

            job_exe.append_stdout(stdout)
            job_exe.append_stderr(stderr)
            job_exe.current_stdout_url = None
            job_exe.current_stderr_url = None
            job_exe.save()

    def task_started(self, job_exe_id, task, when, stdout_url, stderr_url):
        """Updates the given job execution to reflect that the given task has started

        :param job_exe_id: The job execution ID
        :type job_exe_id: int
        :param task: Indicates which task, either 'pre', 'job', or 'post'
        :type task: str
        :param when: The time that the task started
        :type when: :class:`datetime.datetime`
        :param stdout_url: The URL for the task's stdout logs
        :type stdout_url: str
        :param stderr_url: The URL for the task's stderr logs
        :type stderr_url: str
        """

        job_exe_qry = self.filter(id=job_exe_id)

        if task == 'pre':
            job_exe_qry.update(pre_started=when, current_stdout_url=stdout_url, current_stderr_url=stderr_url)
        elif task == 'job':
            job_exe_qry.update(job_started=when, current_stdout_url=stdout_url, current_stderr_url=stderr_url)
        elif task == 'post':
            job_exe_qry.update(post_started=when, current_stdout_url=stdout_url, current_stderr_url=stderr_url)

    def update_status(self, job_exes, status, when, error=None):
        """Updates the given job executions and jobs with the new status. The caller must have obtained model locks on
        the job execution and job models (in that order).

        :param job_exes: The job executions (with related job models) to update
        :type job_exes: [:class:`job.models.JobExecution`]
        :param status: The new status
        :type status: str
        :param when: The time that the status change occurred
        :type when: :class:`datetime.datetime`
        :param error: The error that caused the failure (required if status is FAILED, should be None otherwise)
        :type error: :class:`error.models.Error`
        """

        if status == 'QUEUED':
            raise Exception('QUEUED is an invalid status transition for job executions, use queue_job_exes()')
        if status == 'RUNNING':
            raise Exception('update_status() cannot set a job execution to RUNNING, use schedule_job_executions()')
        if status == 'FAILED' and not error:
            raise Exception('An error is required when status is FAILED')
        if not status == 'FAILED' and error:
            raise Exception('Status %s is invalid with an error' % status)

        modified = timezone.now()

        # Update job execution models in memory and collect job execution IDs
        job_exe_ids = set()
        jobs = []
        for job_exe in job_exes:
            job_exe_ids.add(job_exe.id)
            jobs.append(job_exe.job)
            job_exe.status = status
            job_exe.ended = when
            job_exe.error = error
            job_exe.last_modified = modified

        # Update job execution models in database with single query
        self.filter(id__in=job_exe_ids).update(status=status, ended=when, error=error, last_modified=modified)

        # Update job models
        Job.objects.update_status(jobs, status, when, error)


class JobExecution(models.Model):
    """Represents an instance of a job being queued and executed on a cluster node. Any status updates to a job
    execution model requires obtaining a lock on the model using select_for_update().

    :keyword job: The job that is being executed
    :type job: :class:`django.db.models.ForeignKey`
    :keyword status: The status of the run
    :type status: :class:`django.db.models.CharField`
    :keyword error: The error that caused the failure (should only be set when status is FAILED)
    :type error: :class:`django.db.models.ForeignKey`

    :keyword command_arguments: The argument string to execute on the command line for this job execution. This field is
        populated when the job execution is scheduled to run on a node and is updated when any needed pre-job steps are
        run.
    :type command_arguments: :class:`django.db.models.CharField`
    :keyword timeout: The maximum amount of time to allow this job to run before being killed (in seconds)
    :type timeout: :class:`django.db.models.IntegerField`
    :keyword docker_params: JSON array of 2-tuples (key-value) which will be passed as-is to docker.
    See the mesos prototype file for further information.
    :type docker_params: :class:`djorm_pgjson.fields.JSONField`

    :keyword node: The node on which the job execution is being run
    :type node: :class:`django.db.models.ForeignKey`
    :keyword environment: JSON description defining the environment data for this job execution. This field is populated
        when the job execution is scheduled to run on a node.
    :type environment: :class:`djorm_pgjson.fields.JSONField`
    :keyword cpus_scheduled: The number of CPUs scheduled for this job execution
    :type cpus_scheduled: :class:`django.db.models.FloatField`
    :keyword mem_scheduled: The amount of RAM in MiB scheduled for this job execution
    :type mem_scheduled: :class:`django.db.models.FloatField`
    :keyword disk_in_scheduled: The amount of disk space in MiB scheduled for input files for this job execution
    :type disk_in_scheduled: :class:`django.db.models.FloatField`
    :keyword disk_out_scheduled: The amount of disk space in MiB scheduled for output (temp work and products) for this
        job execution
    :type disk_out_scheduled: :class:`django.db.models.FloatField`
    :keyword disk_total_scheduled: The total amount of disk space in MiB scheduled for this job execution
    :type disk_total_scheduled: :class:`django.db.models.FloatField`
    :keyword requires_cleanup: Whether this job execution still requires cleanup on the node
    :type requires_cleanup: :class:`django.db.models.BooleanField`

    :keyword pre_task_id: The unique ID of the pre-task
    :type pre_task_id: :class:`django.db.models.CharField`
    :keyword pre_started: When the pre-task was started
    :type pre_started: :class:`django.db.models.DateTimeField`
    :keyword pre_completed: When the pre-task was completed
    :type pre_completed: :class:`django.db.models.DateTimeField`
    :keyword pre_exit_code: The exit code of the pre-task
    :type pre_exit_code: :class:`django.db.models.IntegerField`

    :keyword job_task_id: The unique ID of the task running the job
    :type job_task_id: :class:`django.db.models.CharField`
    :keyword job_started: When the main job task started running
    :type job_started: :class:`django.db.models.DateTimeField`
    :keyword job_completed: When the main job task was completed
    :type job_completed: :class:`django.db.models.DateTimeField`
    :keyword job_exit_code: The exit code of the main job task
    :type job_exit_code: :class:`django.db.models.IntegerField`

    :keyword post_task_id: The unique ID of the post-task
    :type post_task_id: :class:`django.db.models.CharField`
    :keyword post_started: When the post-task was started
    :type post_started: :class:`django.db.models.DateTimeField`
    :keyword post_completed: When the post-task was completed
    :type post_completed: :class:`django.db.models.DateTimeField`
    :keyword post_exit_code: The exit code of the post-task
    :type post_exit_code: :class:`django.db.models.IntegerField`

    :keyword stdout: The stdout contents of the entire job execution. This field should normally be deferred when
        querying for job executions since it can be large and often is not needed.
    :type stdout: :class:`django.db.models.TextField`
    :keyword stderr: The stderr contents of the entire job execution. This field should normally be deferred when
        querying for job executions since it can be large and often is not needed.
    :type stderr: :class:`django.db.models.TextField`
    :keyword current_stdout_url: URL for gettng the current stdout log contents
    :type current_stdout_url: :class:`django.db.models.URLField`
    :keyword current_stderr_url: URL for gettng the current stderr log contents
    :type current_stderr_url: :class:`django.db.models.URLField`

    :keyword results_manifest: The results manifest generated by the job's algorithm
    :type results_manifest: :class:`djorm_pgjson.fields.JSONField`
    :keyword results: JSON description defining the results for this job execution. This field is populated when the
        post-job steps are successfully completed.
    :type results: :class:`djorm_pgjson.fields.JSONField`

    :keyword created: When the job execution was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword queued: When the job was added to the queue for this run and went to QUEUED status
    :type queued: :class:`django.db.models.DateTimeField`
    :keyword started: When the job was scheduled and went to RUNNING status
    :type started: :class:`django.db.models.DateTimeField`
    :keyword ended: When the job execution ended (FAILED, COMPLETED, or CANCELED)
    :type ended: :class:`django.db.models.DateTimeField`
    :keyword cleaned_up: When the job execution was cleaned up on the node
    :type cleaned_up: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the job execution was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`
    """
    JOB_EXE_STATUSES = (
        ('QUEUED', 'QUEUED'),
        ('RUNNING', 'RUNNING'),
        ('FAILED', 'FAILED'),
        ('COMPLETED', 'COMPLETED'),
        ('CANCELED', 'CANCELED'),
    )

    FINAL_STATUSES = ['FAILED', 'COMPLETED', 'CANCELED']

    job = models.ForeignKey('job.Job', on_delete=models.PROTECT)
    status = models.CharField(choices=JOB_EXE_STATUSES, default='QUEUED', max_length=50, db_index=True)
    error = models.ForeignKey('error.Error', blank=True, null=True, on_delete=models.PROTECT)

    command_arguments = models.CharField(max_length=1000)
    timeout = models.IntegerField()
    docker_params = djorm_pgjson.fields.JSONField(null=True)

    node = models.ForeignKey('node.Node', blank=True, null=True, on_delete=models.PROTECT)
    environment = djorm_pgjson.fields.JSONField()
    cpus_scheduled = models.FloatField(blank=True, null=True)
    mem_scheduled = models.FloatField(blank=True, null=True)
    disk_in_scheduled = models.FloatField(blank=True, null=True)
    disk_out_scheduled = models.FloatField(blank=True, null=True)
    disk_total_scheduled = models.FloatField(blank=True, null=True)
    requires_cleanup = models.BooleanField(default=False, db_index=True)
    cleanup_job = models.ForeignKey('job.Job', related_name='cleans', blank=True, null=True, on_delete=models.PROTECT)

    pre_task_id = models.CharField(blank=True, max_length=50, null=True)
    pre_started = models.DateTimeField(blank=True, null=True)
    pre_completed = models.DateTimeField(blank=True, null=True)
    pre_exit_code = models.IntegerField(blank=True, null=True)

    job_task_id = models.CharField(blank=True, max_length=50, null=True)
    job_started = models.DateTimeField(blank=True, null=True)
    job_completed = models.DateTimeField(blank=True, null=True)
    job_exit_code = models.IntegerField(blank=True, null=True)
    job_metrics = djorm_pgjson.fields.JSONField(null=True)

    post_task_id = models.CharField(blank=True, max_length=50, null=True)
    post_started = models.DateTimeField(blank=True, null=True)
    post_completed = models.DateTimeField(blank=True, null=True)
    post_exit_code = models.IntegerField(blank=True, null=True)

    stdout = models.TextField(blank=True, null=True)
    stderr = models.TextField(blank=True, null=True)
    current_stdout_url = models.URLField(null=True, max_length=600)
    current_stderr_url = models.URLField(null=True, max_length=600)

    results_manifest = djorm_pgjson.fields.JSONField()
    results = djorm_pgjson.fields.JSONField()

    created = models.DateTimeField(auto_now_add=True)
    queued = models.DateTimeField()
    started = models.DateTimeField(blank=True, null=True)
    ended = models.DateTimeField(blank=True, null=True)
    cleaned_up = models.DateTimeField(blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True, db_index=True)

    objects = JobExecutionManager()

    def get_docker_image(self):
        """Gets the Docker image for the job execution

        :returns: The Docker image for the job execution
        :rtype: str
        """

        return self.job.job_type.docker_image

    def get_docker_params(self):
        """Get the Docker params as a list of lists. Performs some basic validation.

        :returns: The Docker params as a list of lists
        :rtype: list
        """

        if self.docker_params is None or len(self.docker_params) == 0:
            return []
        if type(self.docker_params) is not type([]):
            return []
        if False in map(lambda x: type(x) is type([]) and len(x) == 2, self.docker_params):
            return []
        return self.docker_params

    def get_error_interface(self):
        """Returns the error interface for this job execution

        :returns: The error interface for this job execution
        :rtype: :class:`job.configuration.interface.job_interface.ErrorInterface`
        """

        return self.job.job_type.get_error_interface()

    def get_job_environment(self):
        """Returns the environment data for this job

        :returns: The environment data for this job
        :rtype: :class:`job.configuration.environment.job_environment.JobEnvironment`
        """

        return JobEnvironment(self.environment)

    def get_job_interface(self):
        """Returns the job interface for executing this job

        :returns: The interface for this job execution
        :rtype: :class:`job.configuration.interface.job_interface.JobInterface`
        """

        return self.job.get_job_interface()

    def get_job_results(self):
        """Returns the results for this job execution

        :returns: The results for this job execution
        :rtype: :class:`job.configuration.results.job_results.JobResults`
        """

        return JobResults(self.results)

    def get_job_type_name(self):
        """Returns the name of this job's type

        :returns: The name of this job's type
        :rtype: str
        """

        return self.job.job_type.name

    def is_docker_privileged(self):
        """Indicates whether this job execution uses Docker in privileged mode

        :returns: True if this job execution uses Docker in privileged mode, False otherwise
        :rtype: bool
        """

        return self.job.job_type.docker_privileged

    @property
    def is_finished(self):
        """Indicates if this job execution has completed (success or failure)

        :returns: True if the job execution is in an final state, False otherwise
        :rtype: bool
        """
        return self.status in ['FAILED', 'COMPLETED', 'CANCELED']

    @property
    def is_system(self):
        """Indicates whether this job execution is for a system job

        :returns: True if this job execution is for a system job, False otherwise
        :rtype: bool
        """

        return self.job.job_type.is_system

    def is_timed_out(self, when):
        """Indicates whether this job execution is timed out based on the given current time

        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: True if this job execution is for a system job, False otherwise
        :rtype: bool
        """

        running_with_timeout_set = self.status == 'RUNNING' and self.timeout
        timeout_exceeded = self.started + datetime.timedelta(seconds=self.timeout) < when
        return running_with_timeout_set and timeout_exceeded

    def uses_docker(self):
        """Indicates whether this job execution uses Docker

        :returns: True if this job execution uses Docker, False otherwise
        :rtype: bool
        """

        return self.job.job_type.uses_docker

    def append_stdout(self, stdout):
        """Appends the given string content to the standard output field.

        :param stdout: The standard output content to append.
        :type stdout: str
        :returns: The new standard output log after appending new content.
        :rtype: str
        """
        if stdout:
            if self.stdout:
                self.stdout += stdout
            else:
                self.stdout = stdout
        return self.stdout

    def append_stderr(self, stderr):
        """Appends the given string content to the standard error field.

        :param stderr: The standard error content to append.
        :type stderr: str
        :returns: The new standard error log after appending new content.
        :rtype: str
        """
        if stderr:
            if self.stderr:
                self.stderr += stderr
            else:
                self.stderr = stderr
        return self.stderr

    class Meta(object):
        """Meta information for the database"""
        db_table = 'job_exe'


class JobTypeStatusCounts(object):
    """Represents job counts for a job type.

    :keyword status: The job execution status being counted.
    :type status: str
    :keyword count: The number of job executions for the associated status.
    :type count: int
    :keyword most_recent: The date/time of the last job execution for the associated status.
    :type most_recent: datetime.datetime
    :keyword category: The category of the job execution status being counted. Note that currently this will only be
        populated for types of ERROR status values.
    :type category: str
    """
    def __init__(self, status, count=0, most_recent=None, category=None):
        self.status = status
        self.count = count
        self.most_recent = most_recent
        self.category = category


class JobTypeStatus(object):
    """Represents job type statistics.

    :keyword job_type: The job type being counted.
    :type job_type: :class:`job.models.JobType`
    :keyword job_counts: A list of counts for the jobs of the given job type organized by status.
    :type job_counts: list[:class:`job.models.JobTypeStatusCounts`]
    """
    def __init__(self, job_type, job_counts=None):
        self.job_type = job_type
        self.job_counts = job_counts


class JobTypeRunningStatus(object):
    """Represents job type running statistics.

    :keyword job_type: The job type being counted.
    :type job_type: :class:`job.models.JobType`
    :keyword count: The number of job executions running for the associated job type.
    :type count: int
    :keyword longest_running: The date/time of the last job execution for the associated job type.
    :type longest_running: datetime.datetime
    """
    def __init__(self, job_type, count=0, longest_running=None):
        self.job_type = job_type
        self.count = count
        self.longest_running = longest_running


class JobTypeFailedStatus(object):
    """Represents job type system failure statistics.

    :keyword job_type: The job type being counted.
    :type job_type: :class:`job.models.JobType`
    :keyword count: The number of job executions failed for the associated job type.
    :type count: int
    :keyword first_error: The date/time of the first job execution failed for the associated job type.
    :type first_error: datetime.datetime
    :keyword last_error: The date/time of the last job execution failed for the associated job type.
    :type last_error: datetime.datetime
    """
    def __init__(self, job_type, error, count=0, first_error=None, last_error=None):
        self.job_type = job_type
        self.error = error
        self.count = count
        self.first_error = first_error
        self.last_error = last_error


class JobTypeManager(models.Manager):
    """Provides additional methods for handling job types
    """

    @transaction.atomic
    def create_job_type(self, name, version, interface, trigger_rule=None, error_mapping=None, **kwargs):
        """Creates a new non-system job type and saves it in the database. All database changes occur in an atomic
        transaction.

        :param name: The stable name of the job type used by clients for queries
        :type name: str
        :param version: The version of the job type
        :type version: str
        :param interface: The interface for running a job of this type
        :type interface: :class:`job.configuration.interface.job_interface.JobInterface`
        :param trigger_rule: The trigger rule that creates jobs of this type, possibly None
        :type trigger_rule: :class:`trigger.models.TriggerRule`
        :param error_mapping: Mapping for translating an exit code to an error type
        :type error_mapping: :class:`job.configuration.interface.error_interface.ErrorInterface`
        :returns: The new job type
        :rtype: :class:`job.models.JobType`

        :raises :class:`job.exceptions.InvalidJobField`: If a given job type field has an invalid value
        :raises :class:`trigger.configuration.exceptions.InvalidTriggerType`: If the given trigger rule is an invalid
        type for creating jobs
        :raises :class:`trigger.configuration.exceptions.InvalidTriggerRule`: If the given trigger rule configuration is
        invalid
        :raises :class:`job.configuration.data.exceptions.InvalidConnection`: If the trigger rule connection to the job
        type interface is invalid
        """

        for field_name in kwargs:
            if field_name in JobType.UNEDITABLE_FIELDS:
                raise Exception('%s is not an editable field' % field_name)
        self._validate_job_type_fields(**kwargs)

        # Validate the trigger rule
        if trigger_rule:
            trigger_config = trigger_rule.get_configuration()
            if not isinstance(trigger_config, JobTriggerRuleConfiguration):
                raise InvalidTriggerType('%s is an invalid trigger rule type for creating jobs' % trigger_rule.type)
            trigger_config.validate_trigger_for_job(interface)

        # Create the new job type
        job_type = JobType(**kwargs)
        job_type.name = name
        job_type.version = version
        job_type.interface = interface.get_dict()
        job_type.trigger_rule = trigger_rule
        if error_mapping:
            error_mapping.validate()
            job_type.error_mapping = error_mapping.get_dict()
        if 'is_active' in kwargs:
            job_type.archived = None if kwargs['is_active'] else timezone.now()
        if 'is_paused' in kwargs:
            job_type.paused = timezone.now() if kwargs['is_paused'] else None
        job_type.save()

        # Create first revision of the job type
        JobTypeRevision.objects.create_job_type_revision(job_type)

        return job_type

    @transaction.atomic
    def edit_job_type(self, job_type_id, interface=None, trigger_rule=None, remove_trigger_rule=False,
                      error_mapping=None, **kwargs):
        """Edits the given job type and saves the changes in the database. The caller must provide the related
        trigger_rule model. All database changes occur in an atomic transaction. An argument of None for a field
        indicates that the field should not change. The remove_trigger_rule parameter indicates the difference between
        no change to the trigger rule (False) and removing the trigger rule (True) when trigger_rule is None.

        :param job_type_id: The unique identifier of the job type to edit
        :type job_type_id: int
        :param interface: The interface for running a job of this type, possibly None
        :type interface: :class:`job.configuration.interface.job_interface.JobInterface`
        :param trigger_rule: The trigger rule that creates jobs of this type, possibly None
        :type trigger_rule: :class:`trigger.models.TriggerRule`
        :param remove_trigger_rule: Indicates whether the trigger rule should be unchanged (False) or removed (True)
            when trigger_rule is None
        :type remove_trigger_rule: bool
        :param error_mapping: Mapping for translating an exit code to an error type
        :type error_mapping: :class:`job.configuration.interface.error_interface.ErrorInterface`

        :raises :class:`job.exceptions.InvalidJobField`: If a given job type field has an invalid value
        :raises :class:`trigger.configuration.exceptions.InvalidTriggerType`: If the given trigger rule is an invalid
        type for creating jobs
        :raises :class:`trigger.configuration.exceptions.InvalidTriggerRule`: If the given trigger rule configuration is
        invalid
        :raises :class:`job.configuration.data.exceptions.InvalidConnection`: If the trigger rule connection to the job
        type interface is invalid
        :raises :class:`recipe.configuration.definition.exceptions.InvalidDefinition`: If the interface change
        invalidates any existing recipe type definitions
        """

        for field_name in kwargs:
            if field_name in JobType.UNEDITABLE_FIELDS:
                raise Exception('%s is not an editable field' % field_name)
        self._validate_job_type_fields(**kwargs)

        recipe_types = []
        if interface:
            # Lock all recipe types so they can be validated after changing job type interface
            from recipe.models import RecipeType
            recipe_types = list(RecipeType.objects.select_for_update().order_by('id').iterator())

        # Acquire model lock for job type
        job_type = JobType.objects.select_for_update().get(pk=job_type_id)
        if job_type.is_system:
            raise Exception('Cannot edit a system job type')

        if interface:
            # New job interface, validate all existing recipes
            job_type.interface = interface.get_dict()
            job_type.revision_num = job_type.revision_num + 1
            job_type.save()
            for recipe_type in recipe_types:
                recipe_type.get_recipe_definition().validate_job_interfaces()

        if trigger_rule or remove_trigger_rule:
            if job_type.trigger_rule:
                # Archive old trigger rule since we are changing to a new one
                TriggerRule.objects.archive_trigger_rule(job_type.trigger_rule_id)
            job_type.trigger_rule = trigger_rule

        # Validate updated trigger rule against updated interface
        if job_type.trigger_rule:
            trigger_config = job_type.trigger_rule.get_configuration()
            if not isinstance(trigger_config, JobTriggerRuleConfiguration):
                msg = '%s is an invalid trigger rule type for creating jobs'
                raise InvalidTriggerType(msg % job_type.trigger_rule.type)
            trigger_config.validate_trigger_for_job(job_type.get_job_interface())

        if error_mapping:
            error_mapping.validate()
            job_type.error_mapping = error_mapping.get_dict()
        if 'is_active' in kwargs and job_type.is_active != kwargs['is_active']:
            job_type.archived = None if kwargs['is_active'] else timezone.now()
        if 'is_paused' in kwargs and job_type.is_paused != kwargs['is_paused']:
            job_type.paused = timezone.now() if kwargs['is_paused'] else None
        for field_name in kwargs:
            setattr(job_type, field_name, kwargs[field_name])
        job_type.save()

        if interface:
            # Create new revision of the job type for new interface
            JobTypeRevision.objects.create_job_type_revision(job_type)

    def get_by_natural_key(self, name, version):
        """Django method to retrieve a job type for the given natural key

        :param name: The human-readable name of the job type
        :type name: str
        :param version: The version of the job type
        :type version: str
        :returns: The job type defined by the natural key
        :rtype: :class:`job.models.JobType`
        """
        return self.get(name=name, version=version)

    def get_cleanup_job_type(self):
        """Returns the Scale Cleanup job type

        :returns: The cleanup job type
        :rtype: :class:`job.models.JobType`
        """

        return JobType.objects.get(name='scale-cleanup', version='1.0')

    def get_clock_job_type(self):
        """Returns the Scale Clock job type

        :returns: The clock job type
        :rtype: :class:`job.models.JobType`
        """

        return JobType.objects.get(name='scale-clock', version='1.0')

    def get_job_types(self, started=None, ended=None, names=None, categories=None, order=None):
        """Returns a list of job types within the given time range.

        :param started: Query job types updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query job types updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param names: Query jobs of the type associated with the name.
        :type names: list[str]
        :param categories: Query jobs of the type associated with the category.
        :type categories: list[str]
        :param order: A list of fields to control the sort order.
        :type order: list[str]
        :returns: The list of job types that match the time range.
        :rtype: list[:class:`job.models.JobType`]
        """

        # Fetch a list of job types
        job_types = JobType.objects.all()

        # Apply time range filtering
        if started:
            job_types = job_types.filter(last_modified__gte=started)
        if ended:
            job_types = job_types.filter(last_modified__lte=ended)

        # Apply additional filters
        if names:
            job_types = job_types.filter(name__in=names)
        if categories:
            job_types = job_types.filter(category__in=categories)

        # Apply sorting
        if order:
            job_types = job_types.order_by(*order)
        else:
            job_types = job_types.order_by('last_modified')
        return job_types

    def get_details(self, job_type_id):
        """Returns the job type for the given ID with all detail fields included.

        The additional fields include: errors, job_counts_6h, job_counts_12h, and job_counts_24h.

        :param job_type_id: The unique identifier of the job type.
        :type job_type_id: int
        :returns: The job type with all detail fields included.
        :rtype: :class:`job.models.JobType`
        """

        # Attempt to get the job type
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type_id)

        # Add associated error information
        error_names = job_type.get_error_interface().get_error_names()
        job_type.errors = Error.objects.filter(name__in=error_names) if error_names else []

        # Add recent performance statistics
        started = timezone.now()
        job_type.job_counts_24h = self.get_performance(job_type_id, started - datetime.timedelta(hours=24))
        job_type.job_counts_12h = self.get_performance(job_type_id, started - datetime.timedelta(hours=12))
        job_type.job_counts_6h = self.get_performance(job_type_id, started - datetime.timedelta(hours=6))

        return job_type

    def get_performance(self, job_type_id, started, ended=None):
        """Returns the job count statistics for a given job type and time range.

        :param job_type_id: The unique identifier of the job type.
        :type job_type_id: int
        :returns: A list of job counts organized by status.
        :rtype: list[:class:`job.models.JobTypeStatusCounts`]
        """
        count_dicts = Job.objects.values('job_type__id', 'status', 'error__category')
        count_dicts = count_dicts.filter(job_type_id=job_type_id, last_status_change__gte=started)
        if ended:
            count_dicts = count_dicts.filter(last_status_change__lte=ended)
        count_dicts = count_dicts.annotate(count=models.Count('job_type'),
                                           most_recent=models.Max('last_status_change'))
        results = []
        for count_dict in count_dicts:
            counts = JobTypeStatusCounts(count_dict['status'], count_dict['count'],
                                         count_dict['most_recent'], count_dict['error__category'])
            results.append(counts)
        return results

    def get_status(self, started, ended=None):
        """Returns a list of job types with counts broken down by job status.

        Note that all running job types are counted regardless of date/time filters.

        :param started: Query job types updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query job types updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :returns: The list of job types with supplemented statistics.
        :rtype: list[:class:`job.models.JobTypeStatus`]
        """

        # Build a mapping of all job type identifier -> status model
        job_types = JobType.objects.all().defer('interface', 'error_mapping').order_by('last_modified')
        status_dict = {job_type.id: JobTypeStatus(job_type, []) for job_type in job_types}

        # Build up the filters based on inputs and all running jobs
        count_filters = Q(status='RUNNING')
        if ended:
            count_filters = count_filters | Q(last_status_change__gte=started, last_status_change__lte=ended)
        else:
            count_filters = count_filters | Q(last_status_change__gte=started)

        # Fetch a count of all jobs grouped by status counts
        count_dicts = Job.objects.values('job_type__id', 'status', 'error__category').filter(count_filters)
        count_dicts = count_dicts.annotate(count=models.Count('job_type'),
                                           most_recent=models.Max('last_status_change'))

        # Collect the status and counts by job type
        for count_dict in count_dicts:
            status = status_dict[count_dict['job_type__id']]
            counts = JobTypeStatusCounts(count_dict['status'], count_dict['count'],
                                         count_dict['most_recent'], count_dict['error__category'])
            status.job_counts.append(counts)

        return [status_dict[job_type.id] for job_type in job_types]

    def get_running_status(self):
        """Returns a status overview of all currently running job types.

        The results consist of standard job type models, plus additional computed statistics fields including a total
        count of associated jobs and the longest running job.

        :returns: The list of each job type with additional statistic fields.
        :rtype: list[:class:`job.models.JobTypeRunningStatus`]
        """

        # Make a list of all the basic job type fields to fetch
        job_type_fields = ['id', 'name', 'version', 'title', 'description', 'category', 'is_system',
                           'is_long_running', 'is_active', 'is_operational', 'is_paused', 'icon_code']

        # Fetch a count of all running jobs with type information
        # We have to specify values to workaround the JSON fields throwing an error when used with annotate
        job_dicts = Job.objects.values(*['job_type__%s' % f for f in job_type_fields])
        job_dicts = job_dicts.filter(status='RUNNING')
        job_dicts = job_dicts.annotate(count=models.Count('job_type'),
                                       longest_running=models.Min('last_status_change'))
        job_dicts = job_dicts.order_by('longest_running')

        # Convert each result to a real job type model with added statistics
        results = []
        for job_dict in job_dicts:
            job_type_dict = {f: job_dict['job_type__%s' % f] for f in job_type_fields}
            job_type = JobType(**job_type_dict)

            status = JobTypeRunningStatus(job_type, job_dict['count'], job_dict['longest_running'])
            results.append(status)
        return results

    def get_failed_status(self):
        """Returns all job types that have failed due to system errors.

        The results consist of standard job type models, plus additional computed statistics fields including a total
        count of associated jobs and the last status change of a running job.

        :returns: The list of each job type with additional statistic fields.
        :rtype: list[:class:`job.models.JobTypeFailedStatus`]
        """

        # Make a list of all the basic job type fields to fetch
        job_type_fields = ['id', 'name', 'version', 'title', 'description', 'category', 'is_system',
                           'is_long_running', 'is_active', 'is_operational', 'is_paused', 'icon_code']

        # Make a list of all the basic error fields to fetch
        error_fields = ['id', 'name', 'description', 'category', 'created', 'last_modified']

        # We have to specify values to workaround the JSON fields throwing an error when used with annotate
        query_fields = []
        query_fields.extend(['job_type__%s' % f for f in job_type_fields])
        query_fields.extend(['error__%s' % f for f in error_fields])

        # Fetch a count of all running jobs with type information
        job_dicts = Job.objects.values(*query_fields)
        job_dicts = job_dicts.filter(status='FAILED', error__category='SYSTEM')
        job_dicts = job_dicts.annotate(count=models.Count('job_type'),
                                       first_error=models.Min('last_status_change'),
                                       last_error=models.Max('last_status_change'))
        job_dicts = job_dicts.order_by('-last_error')

        # Convert each result to a real job type model with added statistics
        results = []
        for job_dict in job_dicts:
            job_type_dict = {f: job_dict['job_type__%s' % f] for f in job_type_fields}
            job_type = JobType(**job_type_dict)

            error_dict = {f: job_dict['error__%s' % f] for f in error_fields}
            error = Error(**error_dict)

            status = JobTypeFailedStatus(job_type, error, job_dict['count'], job_dict['first_error'],
                                         job_dict['last_error'])
            results.append(status)
        return results

    def validate_job_type(self, name, version, interface, error_mapping=None, trigger_config=None):
        """Validates a new job type prior to attempting a save

        :param name: The system name of the job type
        :type name: str
        :param version: The version of the job type
        :type version: str
        :param interface: The interface for running a job of this type
        :type interface: :class:`job.configuration.interface.job_interface.JobInterface`
        :param error_mapping: The interface for mapping error exit codes
        :type error_mapping: :class:`job.configuration.interface.error_interface.ErrorInterface`
        :param trigger_config: The trigger rule configuration, possibly None
        :type trigger_config: :class:`trigger.configuration.trigger_rule.TriggerRuleConfiguration`
        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`trigger.configuration.exceptions.InvalidTriggerType`: If the given trigger rule is an invalid
            type for creating jobs
        :raises :class:`trigger.configuration.exceptions.InvalidTriggerRule`: If the given trigger rule configuration is
            invalid
        :raises :class:`job.configuration.data.exceptions.InvalidConnection`: If the trigger rule connection to the job
            type interface is invalid
        :raises :class:`recipe.configuration.definition.exceptions.InvalidDefinition`: If the interface invalidates any
            existing recipe type definitions
        """

        warnings = []

        if trigger_config:
            trigger_config.validate()
            if not isinstance(trigger_config, JobTriggerRuleConfiguration):
                msg = '%s is an invalid trigger rule type for creating jobs'
                raise InvalidTriggerType(msg % trigger_config.trigger_rule_type)
            warnings.extend(trigger_config.validate_trigger_for_job(interface))

        if error_mapping:
            warnings.extend(error_mapping.validate())

        try:
            # If this is an existing job type, try changing the interface temporarily and validate all existing recipe
            # type definitions
            with transaction.atomic():
                job_type = JobType.objects.get(name=name, version=version)
                job_type.interface = interface.get_dict()
                job_type.save()

                from recipe.models import RecipeType
                for recipe_type in RecipeType.objects.all():
                    warnings.extend(recipe_type.get_recipe_definition().validate_job_interfaces())

                # Explicitly roll back transaction so job type isn't changed
                raise RollbackTransaction()
        except (JobType.DoesNotExist, RollbackTransaction):
            # Swallow exceptions
            pass

        return warnings

    def _validate_job_type_fields(self, **kwargs):
        """Validates the given keyword argument fields for job types

        :raises :class:`job.exceptions.InvalidJobField`: If a given job type field has an invalid value
        """

        if 'timeout' in kwargs:
            timeout = kwargs['timeout']
            if not timeout > 0:
                raise InvalidJobField('timeout must be greater than zero')
        if 'max_tries' in kwargs:
            max_tries = kwargs['max_tries']
            if not max_tries > 0:
                raise InvalidJobField('max_tries must be greater than zero')


class JobType(models.Model):
    """Represents a type of job that can be run on the cluster. Any updates to a job type model requires obtaining a
    lock on the model using select_for_update().

    :keyword name: The stable name of the job type used by clients for queries
    :type name: :class:`django.db.models.CharField`
    :keyword version: The version of the job type
    :type version: :class:`django.db.models.CharField`
    :keyword title: The human-readable name of the job type
    :type title: :class:`django.db.models.CharField`
    :keyword description: An optional description of the job type
    :type description: :class:`django.db.models.TextField`
    :keyword category: An optional overall category of the job type
    :type category: :class:`django.db.models.CharField`
    :keyword author_name: The name of the person or organization that created the associated algorithm
    :type author_name: :class:`django.db.models.CharField`
    :keyword author_url: The address to a home page about the author or associated algorithm
    :type author_url: :class:`django.db.models.TextField`

    :keyword is_system: Whether this is a system type
    :type is_system: :class:`django.db.models.BooleanField`
    :keyword is_long_running: Whether this type is long running. A job of this type is intended to run for a long time,
        potentially indefinitely, without timing out and always being re-queued after a failure
    :type is_long_running: :class:`django.db.models.BooleanField`
    :keyword is_active: Whether the job type is active (false once job type is archived)
    :type is_active: :class:`django.db.models.BooleanField`
    :keyword is_operational: Whether this job type is operational (True) or is still in a research & development (R&D)
        phase (False)
    :type is_operational: :class:`django.db.models.BooleanField`
    :keyword is_paused: Whether the job type is paused (while paused no jobs of this type will be scheduled off of the
        queue)
    :type is_paused: :class:`django.db.models.BooleanField`
    :keyword requires_cleanup: Whether a job of this type requires cleanup on the node afer the job runs
    :type requires_cleanup: :class:`django.db.models.BooleanField`

    :keyword uses_docker: Whether the job type uses Docker
    :type uses_docker: :class:`django.db.models.BooleanField`
    :keyword docker_privileged: Whether the job type uses Docker in privileged mode
    :type docker_privileged: :class:`django.db.models.BooleanField`
    :keyword docker_image: The Docker image containing the code to run for this job (if uses_docker is True)
    :type docker_image: :class:`django.db.models.CharField`
    :keyword interface: JSON description defining the interface for running a job of this type
    :type interface: :class:`djorm_pgjson.fields.JSONField`
    :keyword docker_params: JSON array of 2-tuples (key-value) which will be passed as-is to docker.
    See the mesos prototype file for further information.
    :type docker_params: :class:`djorm_pgjson.fields.JSONField`
    :keyword revision_num: The current revision number of the interface, starts at one
    :type revision_num: :class:`django.db.models.IntegerField`
    :keyword error_mapping: Mapping for translating an exit code to an error type
    :type error_mapping: :class:`djorm_pgjson.fields.JSONField`
    :keyword trigger_rule: The rule to trigger new jobs of this type
    :type trigger_rule: :class:`django.db.models.ForeignKey`

    :keyword priority: The priority of the job type (lower number is higher priority)
    :type priority: :class:`django.db.models.IntegerField`
    :keyword max_scheduled: The maximum number of jobs of this type that may be scheduled to run at the same time
    :type max_scheduled: :class:`django.db.models.IntegerField`
    :keyword timeout: The maximum amount of time to allow a job of this type to run before being killed (in seconds)
    :type timeout: :class:`django.db.models.IntegerField`
    :keyword max_tries: The maximum number of times to try executing a job in case of errors (minimum one)
    :type max_tries: :class:`django.db.models.IntegerField`
    :keyword cpus_required: The number of CPUs required for a job of this type
    :type cpus_required: :class:`django.db.models.FloatField`
    :keyword mem_required: The amount of RAM in MiB required for a job of this type
    :type mem_required: :class:`django.db.models.FloatField`
    :keyword disk_out_const_required: A constant amount of disk space in MiB required for job output (temp work and
        products) for a job of this type
    :type disk_out_const_required: :class:`django.db.models.FloatField`
    :keyword disk_out_mult_required: A multiplier (2x = 2.0) applied to the size of the input files to determine
        additional disk space in MiB required for job output (temp work and products) for a job of this type
    :type disk_out_mult_required: :class:`django.db.models.FloatField`

    :keyword icon_code: A font-awesome icon code (like 'f013' for gear) to use when representing this job type
    :type icon_code: str of a FontAwesome icon code

    :keyword created: When the job type was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword archived: When the job type was archived (no longer active)
    :type archived: :class:`django.db.models.DateTimeField`
    :keyword paused: When the job type was paused
    :type paused: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the job type was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`
    """

    UNEDITABLE_FIELDS = ('name', 'version', 'is_system', 'is_long_running', 'is_active', 'requires_cleanup',
                         'uses_docker', 'revision_num', 'created', 'archived', 'paused', 'last_modified')

    name = models.CharField(db_index=True, max_length=50)
    version = models.CharField(db_index=True, max_length=50)
    title = models.CharField(blank=True, max_length=50, null=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(db_index=True, blank=True, max_length=50, null=True)
    author_name = models.CharField(blank=True, max_length=50, null=True)
    author_url = models.TextField(blank=True, null=True)

    is_system = models.BooleanField(default=False)
    is_long_running = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_operational = models.BooleanField(default=True)
    is_paused = models.BooleanField(default=False)
    requires_cleanup = models.BooleanField(default=True)

    uses_docker = models.BooleanField(default=True)
    docker_privileged = models.BooleanField(default=False)
    docker_image = models.CharField(blank=True, null=True, max_length=500)
    interface = djorm_pgjson.fields.JSONField()
    docker_params = djorm_pgjson.fields.JSONField(null=True)
    revision_num = models.IntegerField(default=1)
    error_mapping = djorm_pgjson.fields.JSONField()
    trigger_rule = models.ForeignKey('trigger.TriggerRule', blank=True, null=True, on_delete=models.PROTECT)

    priority = models.IntegerField(default=100)
    max_scheduled = models.IntegerField(blank=True, null=True)
    timeout = models.IntegerField(default=1800)
    max_tries = models.IntegerField(default=3)
    cpus_required = models.FloatField(default=1.0)
    mem_required = models.FloatField(default=64.0)
    disk_out_const_required = models.FloatField(default=64.0)
    disk_out_mult_required = models.FloatField(default=0.0)

    icon_code = models.CharField(max_length=20, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    archived = models.DateTimeField(blank=True, null=True)
    paused = models.DateTimeField(blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = JobTypeManager()

    def get_job_interface(self):
        """Returns the interface for running jobs of this type

        :returns: The job interface for this type
        :rtype: :class:`job.configuration.interface.job_interface.JobInterface`
        """

        return JobInterface(self.interface)

    def get_error_interface(self):
        """Returns the interface for mapping a job's exit code or
        stderr/stdout expression to an error type"""

        return ErrorInterface(self.error_mapping)

    def natural_key(self):
        """Django method to define the natural key for a job type as the
        combination of name and version

        :returns: A tuple representing the natural key
        :rtype: tuple(str, str)
        """
        return (self.name, self.version)

    class Meta(object):
        """meta information for the db"""
        db_table = 'job_type'
        unique_together = ('name', 'version')


class JobTypeRevisionManager(models.Manager):
    """Provides additional methods for handling job type revisions
    """

    def create_job_type_revision(self, job_type):
        """Creates a new revision for the given job type. The job type's interface and revision number must already be
        updated. The caller must have obtained a lock using select_for_update() on the given job type model.

        :param job_type: The job type
        :type job_type: :class:`job.models.JobType`
        """

        new_rev = JobTypeRevision()
        new_rev.job_type = job_type
        new_rev.revision_num = job_type.revision_num
        new_rev.interface = job_type.interface
        new_rev.save()

    def get_by_natural_key(self, job_type, revision_num):
        """Django method to retrieve a job type revision for the given natural key

        :param job_type: The job type
        :type job_type: :class:`job.models.JobType`
        :param revision_num: The revision number
        :type revision_num: int
        :returns: The job type revision defined by the natural key
        :rtype: :class:`job.models.JobTypeRevision`
        """

        return self.get(job_type_id=job_type.id, revision_num=revision_num)

    def get_revision(self, job_type_id, revision_num):
        """Returns the revision for the given job type and revision number

        :param job_type_id: The ID of the job type
        :type job_type_id: int
        :param revision_num: The revision number
        :type revision_num: int
        :returns: The revision
        :rtype: :class:`job.models.JobTypeRevision`
        """

        return JobTypeRevision.objects.get(job_type_id=job_type_id, revision_num=revision_num)


class JobTypeRevision(models.Model):
    """Represents a revision of a job type. New revisions are created when the interface of a job type changes. Any
    inserts of a job type revision model requires obtaining a lock using select_for_update() on the corresponding job
    type model.

    :keyword job_type: The job type for this revision
    :type job_type: :class:`django.db.models.ForeignKey`
    :keyword revision_num: The number for this revision, starting at one
    :type revision_num: :class:`django.db.models.IntegerField`
    :keyword interface: The JSON interface for this revision of the job type
    :type interface: :class:`djorm_pgjson.fields.JSONField`
    :keyword created: When this revision was created
    :type created: :class:`django.db.models.DateTimeField`
    """

    job_type = models.ForeignKey('job.JobType', on_delete=models.PROTECT)
    revision_num = models.IntegerField()
    interface = djorm_pgjson.fields.JSONField()
    created = models.DateTimeField(auto_now_add=True)

    objects = JobTypeRevisionManager()

    def get_job_interface(self):
        """Returns the job type interface for this revision

        :returns: The job type interface for this revision
        :rtype: :class:`job.configuration.interface.job_interface.JobInterface`
        """

        return JobInterface(self.interface)

    def natural_key(self):
        """Django method to define the natural key for a job type revision as the combination of job type and revision
        number

        :returns: A tuple representing the natural key
        :rtype: tuple(str, int)
        """

        return (self.job_type, self.revision_num)

    class Meta(object):
        """meta information for the db"""
        db_table = 'job_type_revision'
        unique_together = ('job_type', 'revision_num')
