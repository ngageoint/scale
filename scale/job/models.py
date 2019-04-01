"""Defines the database models for jobs and job types"""
from __future__ import absolute_import
from __future__ import unicode_literals

import copy
import datetime
import logging
import math
import operator
import re
import semver
from collections import namedtuple

import django.contrib.postgres.fields
import django.utils.html
from django.conf import settings
from django.db import connection, models, transaction
from django.db.models import F, Q
from django.utils import dateparse, timezone

import util.parse
from data.data.json.data_v1 import convert_data_to_v1_json
from data.data.json.data_v6 import convert_data_to_v6_json, DataV6
from data.interface.interface import Interface
from data.interface.parameter import FileParameter, JsonParameter
from error.models import Error
from job.configuration.data.job_data import JobData as JobData_1_0
from job.configuration.exceptions import InvalidJobConfiguration
from job.configuration.configuration import JobConfiguration
from job.configuration.json.job_config_2_0 import convert_config_to_v2_json, JobConfigurationV2
from job.configuration.json.job_config_v6 import convert_config_to_v6_json, JobConfigurationV6
from job.configuration.results.job_results import JobResults as JobResults_1_0
from job.data.job_data import JobData
from job.deprecation import JobInterfaceSunset, JobDataSunset
from job.exceptions import InvalidJobField, NonSeedJobType
from job.execution.configuration.json.exe_config import ExecutionConfiguration
from job.execution.tasks.exe_task import JOB_TASK_ID_PREFIX
from job.execution.tasks.json.results.task_results import TaskResults
from job.seed.manifest import SeedManifest
from job.seed.exceptions import InvalidSeedManifestDefinition
from job.seed.results.job_results import JobResults
from messaging.manager import CommandMessageManager
from node.resources.json.resources import Resources
from node.resources.node_resources import NodeResources
from node.resources.resource import Cpus, Disk, Mem, ScalarResource
from storage.models import ScaleFile
from util import rest as rest_utils
from util.exceptions import RollbackTransaction
from util.validation import ValidationWarning
from vault.secrets_handler import SecretsHandler


logger = logging.getLogger(__name__)


# Required resource minimums for jobs (e.g. resources required for pre and post tasks)
# TODO: We can roll-up these specific minimums in deference to MIN_RESOURCE dict in v6
MIN_CPUS = 0.25
MIN_MEM = 128.0
MIN_DISK = 0.0

MIN_RESOURCE = {
    'cpus': MIN_CPUS,
    'mem': MIN_MEM,
    'disk': MIN_DISK,
    'sharedmem': 0.0
}

INPUT_FILE_BATCH_SIZE = 500  # Maximum batch size for creating JobInputFile models

# IMPORTANT NOTE: Locking order
# Always adhere to the following model order for obtaining row locks via select_for_update() in order to prevent
# deadlocks and ensure query efficiency
# When editing a job/recipe type: RecipeType, JobType

JobTypeValidation = namedtuple('JobTypeValidation', ['is_valid', 'errors', 'warnings'])
JobTypeKey = namedtuple('JobTypeKey', ['name', 'version'])

class JobManager(models.Manager):
    """Provides additional methods for handling jobs
    """

    def create_job_v6(self, job_type_rev, event_id=None, ingest_event_id=None, input_data=None, root_recipe_id=None, recipe_id=None, batch_id=None,
                      superseded_job=None, job_config=None):
        """Creates a new job for the given job type revision and returns the (unsaved) job model

        :param job_type_rev: The job type revision (with populated job_type model) of the job to create
        :type job_type_rev: :class:`job.models.JobTypeRevision`
        :param event_id: The event ID that triggered the creation of this job
        :type event_id: int
        :param ingest_event_id: The ingest event that triggered the creation of this job
        :type ingest_event_id: int
        :param input_data: The job's input data (optional)
        :type input_data: :class:`data.data.data.Data`
        :param root_recipe_id: The ID of the root recipe that contains this job
        :type root_recipe_id: int
        :param recipe_id: The ID of the original recipe that created this job
        :type recipe_id: int
        :param batch_id: The ID of the batch that contains this job
        :type batch_id: int
        :param superseded_job: The job that the created job is superseding, possibly None
        :type superseded_job: :class:`job.models.Job`
        :param job_config: The configuration overrides for running this job, possibly None
        :type job_config: :class:`job.configuration.configuration.JobConfiguration`
        :returns: The new job model
        :rtype: :class:`job.models.Job`

        :raises :class:`data.data.exceptions.InvalidData`: If the input data is invalid
        """

        job = Job()
        job.job_type = job_type_rev.job_type
        job.job_type_rev = job_type_rev
        job.event_id = event_id
        job.ingest_event_id = ingest_event_id
        job.root_recipe_id = root_recipe_id if root_recipe_id else recipe_id
        job.recipe_id = recipe_id
        job.batch_id = batch_id
        job.max_tries = job_type_rev.job_type.max_tries

        if input_data:
            input_data.validate(job_type_rev.get_input_interface())
            job.input = convert_data_to_v6_json(input_data).get_dict()

        if job_config:
            if JobInterfaceSunset.is_seed_dict(job_type_rev.manifest):
                manifest = SeedManifest(job_type_rev.manifest)
                job_config.validate(manifest)
                _ = job_config.remove_secret_settings(manifest)
                job.configuration = convert_config_to_v6_json(job_config).get_dict()
            else:
                interface = job_type_rev.manifest
                job_config.validate_old(interface)
                job.configuration = convert_config_to_v6_json(job_config).get_dict()

        # TODO: remove this legacy job types are removed
        if not JobInterfaceSunset.is_seed_dict(job_type_rev.manifest):
            job.priority = job_type_rev.job_type.priority
            job.timeout = job_type_rev.job_type.timeout

        if superseded_job:
            root_id = superseded_job.root_superseded_job_id
            if not root_id:
                root_id = superseded_job.id
            job.root_superseded_job_id = root_id
            job.superseded_job = superseded_job

        return job

    def create_job_old(self, job_type, event_id, root_recipe_id=None, recipe_id=None, batch_id=None,
                       superseded_job=None, delete_superseded=True):
        """Creates a new job for the given type and returns the job model. Optionally a job can be provided that the new
        job is superseding. The returned job model will have not yet been saved in the database.

        :param job_type: The type of the job to create
        :type job_type: :class:`job.models.JobType`
        :param event_id: The event ID that triggered the creation of this job
        :type event_id: int
        :param root_recipe_id: The ID of the root recipe that contains this job
        :type root_recipe_id: int
        :param recipe_id: The ID of the original recipe that created this job
        :type recipe_id: int
        :param batch_id: The ID of the batch that contains this job
        :type batch_id: int
        :param superseded_job: The job that the created job is superseding, possibly None
        :type superseded_job: :class:`job.models.Job`
        :param delete_superseded: Whether the created job should delete products from the superseded job
        :type delete_superseded: :class:`job.models.Job`
        :returns: The new job
        :rtype: :class:`job.models.Job`
        """

        if not job_type.is_active:
            raise Exception('Job type is no longer active')

        job = Job()
        job.job_type = job_type
        job.job_type_rev = JobTypeRevision.objects.get_revision(job_type.name, job_type.version, job_type.revision_num)
        job.event_id = event_id
        job.root_recipe_id = root_recipe_id if root_recipe_id else recipe_id
        job.recipe_id = recipe_id
        job.batch_id = batch_id
        job.max_tries = job_type.max_tries

        if JobInterfaceSunset.is_seed_dict(job_type.manifest):
            job.timeout = SeedManifest(job_type.manifest).get_timeout()
        else:
            job.priority = job_type.priority
            job.timeout = job_type.timeout

        if superseded_job:
            root_id = superseded_job.root_superseded_job_id
            if not root_id:
                root_id = superseded_job.id
            job.root_superseded_job_id = root_id
            job.superseded_job = superseded_job
            job.delete_superseded = delete_superseded

        return job

    def filter_jobs(self, started=None, ended=None, source_started=None, source_ended=None, source_sensor_classes=None,
                    source_sensors=None, source_collections=None, source_tasks=None,statuses=None, job_ids=None,
                    job_type_ids=None, job_type_names=None,job_type_categories=None, batch_ids=None, recipe_ids=None,
                    error_categories=None, error_ids=None, is_superseded=False, order=None):
        """Returns a query for job models that filters on the given fields

        :param started: Query jobs updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query jobs updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param source_started: Query jobs where source collection started after this time.
        :type source_started: :class:`datetime.datetime`
        :param source_ended: Query jobs where source collection ended before this time.
        :type source_ended: :class:`datetime.datetime`
        :param source_sensor_classes: Query jobs with the given source sensor class.
        :type source_sensor_classes: list
        :param source_sensor: Query jobs with the given source sensor.
        :type source_sensor: list
        :param source_collection: Query jobs with the given source class.
        :type source_collection: list
        :param source_tasks: Query jobs with the given source tasks.
        :type source_tasks: list
        :param statuses: Query jobs with the a specific status.
        :type statuses: list
        :param job_ids: Query jobs associated with the identifier.
        :type job_ids: list
        :param job_type_ids: Query jobs of the type associated with the identifier.
        :type job_type_ids: list
        :param job_type_names: Query jobs of the type associated with the name.
        :type job_type_names: list
        :param job_type_categories: Query jobs of the type associated with the category.
        :type job_type_categories: list
        :param batch_ids: Query jobs associated with the given batch identifiers.
        :type batch_ids: list
        :param recipe_ids: Query jobs associated with the given recipe identifiers.
        :type recipe_ids: list[int]
        :param error_categories: Query jobs that failed due to errors associated with the category.
        :type error_categories: list
        :param error_ids: Query jobs that failed due to these errors.
        :type error_ids: list
        :param is_superseded: Query jobs that match the is_superseded flag.
        :type is_superseded: bool
        :param order: A list of fields to control the sort order.
        :type order: list
        :returns: The job query
        :rtype: :class:`django.db.models.QuerySet`
        """

        # Fetch a list of jobs
        jobs = self.all()

        # Apply time range filtering
        if started:
            jobs = jobs.filter(last_modified__gte=started)
        if ended:
            jobs = jobs.filter(last_modified__lte=ended)

        if source_started:
            jobs = jobs.filter(source_started__gte=source_started)
        if source_ended:
            jobs = jobs.filter(source_ended__lte=source_ended)

        if source_sensor_classes:
            jobs = jobs.filter(source_sensor_class__in=source_sensor_classes)
        if source_sensors:
            jobs = jobs.filter(source_sensor__in=source_sensors)
        if source_collections:
            jobs = jobs.filter(source_collection__in=source_collections)
        if source_tasks:
            jobs = jobs.filter(source_task__in=source_tasks)

        # Apply additional filters
        if statuses:
            jobs = jobs.filter(status__in=statuses)
        if job_ids:
            jobs = jobs.filter(id__in=job_ids)
        if job_type_ids:
            jobs = jobs.filter(job_type_id__in=job_type_ids)
        if job_type_names:
            jobs = jobs.filter(job_type__name__in=job_type_names)
        if job_type_categories:
            jobs = jobs.filter(job_type__category__in=job_type_categories)
        if batch_ids:
            jobs = jobs.filter(batch_id__in=batch_ids)
        if recipe_ids:
            jobs = jobs.filter(recipe_id__in=recipe_ids)
        if error_categories:
            jobs = jobs.filter(error__category__in=error_categories)
        if error_ids:
            jobs = jobs.filter(error_id__in=error_ids)
        if is_superseded is not None:
            jobs = jobs.filter(is_superseded=is_superseded)

        # Apply sorting
        if order:
            jobs = jobs.order_by(*order)
        else:
            jobs = jobs.order_by('last_modified')

        return jobs

    def filter_jobs_related_v5(self, started=None, ended=None, statuses=None, job_ids=None, job_type_ids=None,
                               job_type_names=None, job_type_categories=None, batch_ids=None, error_categories=None,
                               include_superseded=False, order=None):
        """Returns a query for job models that filters on the given fields. The returned query includes the related
        job_type, job_type_rev, event, and error fields, except for the job_type.manifest and job_type_rev.manifest
        fields.

        :param started: Query jobs updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query jobs updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param statuses: Query jobs with the a specific execution status.
        :type statuses: [string]
        :param job_ids: Query jobs associated with the identifier.
        :type job_ids: [int]
        :param job_type_ids: Query jobs of the type associated with the identifier.
        :type job_type_ids: [int]
        :param job_type_names: Query jobs of the type associated with the name.
        :type job_type_names: [string]
        :param job_type_categories: Query jobs of the type associated with the category.
        :type job_type_categories: [string]
        :param batch_ids: Query jobs associated with the given batch identifiers.
        :type batch_ids: list[int]
        :param error_categories: Query jobs that failed due to errors associated with the category.
        :type error_categories: [string]
        :param include_superseded: Whether to include jobs that are superseded.
        :type include_superseded: bool
        :param order: A list of fields to control the sort order.
        :type order: [string]
        :returns: The job query
        :rtype: :class:`django.db.models.QuerySet`
        """

        is_superseded = False
        if include_superseded and include_superseded == True:
            # don't filter out superseded jobs
            is_superseded = None

        jobs = self.filter_jobs(started=started, ended=ended, statuses=statuses, job_ids=job_ids,
                                job_type_ids=job_type_ids, job_type_names=job_type_names,
                                job_type_categories=job_type_categories, batch_ids=batch_ids,
                                error_categories=error_categories, is_superseded=is_superseded,
                                order=order)
        jobs = jobs.select_related('job_type', 'job_type_rev', 'event', 'node', 'error')
        jobs = jobs.defer('job_type__manifest', 'job_type_rev__job_type', 'job_type_rev__manifest')
        return jobs

    def filter_jobs_related_v6(self, started=None, ended=None, source_started=None, source_ended=None,
                               source_sensor_classes=None, source_sensors=None, source_collections=None,
                               source_tasks=None, statuses=None, job_ids=None, job_type_ids=None,
                               job_type_names=None, batch_ids=None, recipe_ids=None, error_categories=None,
                               error_ids=None, is_superseded=None, order=None):
        """Returns a query for job models that filters on the given fields. The returned query includes the related
        job_type, job_type_rev, event, and error fields, except for the job_type.manifest and job_type_rev.manifest
        fields.

        :param started: Query jobs updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query jobs updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param source_started: Query jobs where source collection started after this time.
        :type source_started: :class:`datetime.datetime`
        :param source_ended: Query jobs where source collection ended before this time.
        :type source_ended: :class:`datetime.datetime`
        :param source_sensor_classes: Query jobs with the given source sensor class.
        :type source_sensor_classes: list
        :param source_sensor: Query jobs with the given source sensor.
        :type source_sensor: list
        :param source_collection: Query jobs with the given source class.
        :type source_collection: list
        :param source_tasks: Query jobs with the given source tasks.
        :type source_tasks: list
        :param statuses: Query jobs with the a specific execution status.
        :type statuses: [string]
        :param job_ids: Query jobs associated with the identifier.
        :type job_ids: [int]
        :param job_type_ids: Query jobs of the type associated with the identifier.
        :type job_type_ids: [int]
        :param job_type_names: Query jobs of the type associated with the name.
        :type job_type_names: [string]
        :param batch_ids: Query jobs associated with the given batch identifiers.
        :type batch_ids: list[int]
        :param recipe_ids: Query jobs associated with the given recipe identifiers.
        :type recipe_ids: list[int]
        :param error_categories: Query jobs that failed due to errors associated with the category.
        :type error_categories: [string]
        :param error_ids: Query jobs that failed with errors with the given identifiers.
        :type error_ids: list[int]
        :param is_superseded: Query jobs that match the is_superseded flag.
        :type is_superseded: bool
        :param order: A list of fields to control the sort order.
        :type order: [string]
        :returns: The job query
        :rtype: :class:`django.db.models.QuerySet`
        """

        jobs = self.filter_jobs(started=started, ended=ended, source_started=source_started, source_ended=source_ended,
                                source_sensor_classes=source_sensor_classes, source_sensors=source_sensors,
                                source_collections=source_collections, source_tasks=source_tasks, statuses=statuses,
                                job_ids=job_ids, job_type_ids=job_type_ids,  job_type_names=job_type_names,
                                batch_ids=batch_ids, recipe_ids=recipe_ids, error_ids=error_ids,
                                error_categories=error_categories, is_superseded=is_superseded,
                                order=order)
        jobs = jobs.select_related('job_type', 'job_type_rev', 'event', 'recipe', 'batch', 'node', 'error')
        jobs = jobs.defer('job_type__manifest', 'job_type_rev__job_type', 'job_type_rev__manifest',
                          'recipe__recipe_type', 'recipe__recipe_type_rev', 'recipe__event')
        return jobs

    def get_basic_jobs(self, job_ids):
        """Returns the basic job models for the given IDs with no related fields

        :param job_ids: The job IDs
        :type job_ids: list
        :returns: The job models
        :rtype: list
        """

        return list(self.filter(id__in=job_ids))

    def get_jobs_v5(self, started=None, ended=None, statuses=None, job_ids=None, job_type_ids=None,
                    job_type_names=None, job_type_categories=None, batch_ids=None, error_categories=None,
                    include_superseded=False, order=None):
        """Returns a list of jobs within the given time range.

        :param started: Query jobs updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query jobs updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param statuses: Query jobs with the a specific execution status.
        :type statuses: [string]
        :param job_ids: Query jobs associated with the identifier.
        :type job_ids: [int]
        :param job_type_ids: Query jobs of the type associated with the identifier.
        :type job_type_ids: [int]
        :param job_type_names: Query jobs of the type associated with the name.
        :type job_type_names: [string]
        :param job_type_categories: Query jobs of the type associated with the category.
        :type job_type_categories: [string]
        :param batch_ids: Query jobs associated with batches with the given identifiers.
        :type batch_ids: list[int]
        :param error_categories: Query jobs that failed due to errors associated with the category.
        :type error_categories: [string]
        :param include_superseded: Whether to include jobs that are superseded.
        :type include_superseded: bool
        :param order: A list of fields to control the sort order.
        :type order: [string]
        :returns: The list of jobs that match the time range.
        :rtype: [:class:`job.models.Job`]
        """

        return self.filter_jobs_related_v5(started=started, ended=ended, statuses=statuses, job_ids=job_ids,
                                           job_type_ids=job_type_ids, job_type_names=job_type_names,
                                           job_type_categories=job_type_categories, batch_ids=batch_ids,
                                           error_categories=error_categories, include_superseded=include_superseded,
                                           order=order)

    def get_jobs_v6(self, started=None, ended=None, source_started=None, source_ended=None, source_sensor_classes=None,
                    source_sensors=None, source_collections=None, source_tasks=None, statuses=None, job_ids=None,
                    job_type_ids=None, job_type_names=None, batch_ids=None, recipe_ids=None, error_categories=None,
                    error_ids=None, is_superseded=None, order=None):
        """Returns a list of jobs within the given time range.

        :param started: Query jobs updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query jobs updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param source_started: Query jobs where source collection started after this time.
        :type source_started: :class:`datetime.datetime`
        :param source_ended: Query jobs where source collection ended before this time.
        :type source_ended: :class:`datetime.datetime`
        :param source_sensor_classes: Query jobs with the given source sensor class.
        :type source_sensor_classes: list
        :param source_sensor: Query jobs with the given source sensor.
        :type source_sensor: list
        :param source_collection: Query jobs with the given source class.
        :type source_collection: list
        :param source_tasks: Query jobs with the given source task.
        :type source_tasks: list
        :param statuses: Query jobs with the a specific execution status.
        :type statuses: [string]
        :param job_ids: Query jobs associated with the identifier.
        :type job_ids: [int]
        :param job_type_ids: Query jobs of the type associated with the identifier.
        :type job_type_ids: [int]
        :param job_type_names: Query jobs of the type associated with the name.
        :type job_type_names: [string]
        :param batch_ids: Query jobs associated with batches with the given identifiers.
        :type batch_ids: list[int]
        :param recipe_ids: Query jobs associated with recipes with the given identifiers.
        :type recipe_ids: list[int]
        :param error_categories: Query jobs that failed due to errors associated with the category.
        :type error_categories: [string]
        :param error_ids: Query jobs that failed with errors with the given identifiers.
        :type error_ids: list[int]
        :param is_superseded: Query jobs that match the is_superseded flag.
        :type is_superseded: bool
        :param order: A list of fields to control the sort order.
        :type order: [string]
        :returns: The list of jobs that match the time range.
        :rtype: [:class:`job.models.Job`]
        """

        return self.filter_jobs_related_v6(started=started, ended=ended, source_started=source_started,
                                           source_ended=source_ended, source_sensor_classes=source_sensor_classes,
                                           source_sensors=source_sensors, source_collections=source_collections,
                                           source_tasks=source_tasks, statuses=statuses, job_ids=job_ids,
                                           job_type_ids=job_type_ids, job_type_names=job_type_names,
                                           batch_ids=batch_ids, recipe_ids=recipe_ids,
                                           error_categories=error_categories, error_ids=error_ids,
                                           is_superseded=is_superseded,
                                           order=order)

    def get_details(self, job_id):
        """Gets additional details for the given job model based on related model attributes.

        The additional fields include: input files, recipe, job executions, and generated products.

        :param job_id: The unique identifier of the job.
        :type job_id: int
        :returns: The job with extra related attributes.
        :rtype: :class:`job.models.Job`
        """

        # Attempt to fetch the requested job
        job = Job.objects.select_related(
            'job_type', 'job_type_rev', 'job_type_rev__job_type', 'event', 'error',
            'batch', 'node',
            'superseded_job', 'superseded_job__job_type',
            'superseded_by_job', 'superseded_by_job__job_type'
        ).get(pk=job_id)

        # Attempt to get related job executions
        if job.status in ['RUNNING', 'COMPLETED', 'FAILED', 'QUEUED']:
            try:
                job.execution = JobExecution.objects.get_job_exe_details(job_id=job.id, exe_num=job.num_exes)
            except JobExecution.DoesNotExist:
                job.execution = None
        else:
            job.execution = None

        # Attempt to get related recipe
        # Use a localized import to make higher level application dependencies optional
        try:
            from recipe.models import RecipeNode

            recipe_job = RecipeNode.objects.select_related('recipe', 'recipe__recipe_type', 'recipe__recipe_type_rev',
                                                           'recipe__recipe_type_rev__recipe_type').get(job=job,
                                                                                      recipe__is_superseded=False)
            job.recipe = recipe_job.recipe
        except RecipeNode.DoesNotExist:
            job.recipe = None

        return job

    # TODO: remove this function when API v5 is removed
    def get_details_v5(self, job_id):
        """Gets additional details for the given job model based on related model attributes.

        The additional fields include: input files, recipe, job executions, and generated products.

        :param job_id: The unique identifier of the job.
        :type job_id: int
        :returns: The job with extra related attributes.
        :rtype: :class:`job.models.Job`
        """

        # Attempt to fetch the requested job
        job = Job.objects.select_related(
            'job_type', 'job_type_rev', 'job_type_rev__job_type', 'event', 'event__rule', 'error',
            'root_superseded_job', 'root_superseded_job__job_type', 'superseded_job', 'superseded_job__job_type',
            'superseded_by_job', 'superseded_by_job__job_type'
        ).get(pk=job_id)

        # Attempt to get related job executions
        job_exes = JobExecution.objects.filter(job=job).select_related('job', 'node', 'error')
        job.job_exes = job_exes.defer('job__input', 'job__output').order_by('-created')

        # Attempt to get related recipe
        # Use a localized import to make higher level application dependencies optional
        try:
            from recipe.models import RecipeNode
            recipe_jobs = RecipeNode.objects.filter(job=job).order_by('recipe__last_modified')
            recipe_jobs = recipe_jobs.select_related('recipe', 'recipe__recipe_type', 'recipe__recipe_type_rev',
                                                     'recipe__recipe_type_rev__recipe_type', 'recipe__event',
                                                     'recipe__event__rule')
            job.recipes = [recipe_job.recipe for recipe_job in recipe_jobs]
        except:
            job.recipes = []

        # Fetch all the associated input files
        input_file_ids = job.get_job_data().get_input_file_ids()
        input_files = ScaleFile.objects.filter(id__in=input_file_ids)
        input_files = input_files.select_related('workspace', 'job_type', 'job', 'job_exe')
        input_files = input_files.defer('workspace__json_config', 'job__input', 'job__output', 'job_exe__environment',
                                        'job_exe__configuration', 'job_exe__job_metrics', 'job_exe__stdout',
                                        'job_exe__stderr', 'job_exe__results', 'job_exe__results_manifest',
                                        'job_type__manifest', 'job_type__docker_params', 'job_type__configuration',
                                        'job_type__error_mapping')
        input_files = input_files.prefetch_related('countries')
        input_files = input_files.order_by('id').distinct('id')

        # Attempt to get related products
        output_files = ScaleFile.objects.filter(job=job)
        output_files = output_files.select_related('workspace', 'job_type', 'job', 'job_exe')
        output_files = output_files.defer('workspace__json_config', 'job__input', 'job__output', 'job_exe__environment',
                                          'job_exe__configuration', 'job_exe__job_metrics', 'job_exe__stdout',
                                          'job_exe__stderr', 'job_exe__results', 'job_exe__results_manifest',
                                          'job_type__manifest', 'job_type__docker_params', 'job_type__configuration',
                                          'job_type__error_mapping')
        output_files = output_files.prefetch_related('countries')
        output_files = output_files.order_by('id').distinct('id')

        # Merge job manifest definitions with mapped values
        job_interface = job.get_job_interface()
        job_interface_dict = job_interface.get_dict()
        job_data = job.get_job_data()
        job_data_dict = job_data.get_dict()
        job_results = job.get_job_results()
        job_results_dict = job_results.get_dict()

        if JobInterfaceSunset.is_seed_dict(job_interface_dict):
            job.inputs = job_data.extend_interface_with_inputs_v5(job_interface, input_files)
            job.outputs = job_results.extend_interface_with_outputs_v5(job_interface, output_files)
        else:
            job.inputs = self._merge_job_data(job_interface_dict['input_data'], job_data_dict['input_data'],
                                              input_files)
            job.outputs = self._merge_job_data(job_interface_dict['output_data'], job_results_dict['output_data'],
                                               output_files)


        return job

    # TODO: remove when REST API v5 is removed
    def get_job_updates(self, started=None, ended=None, statuses=None, job_type_ids=None,
                        job_type_names=None, job_type_categories=None, include_superseded=False, order=None):
        """Returns a list of jobs that changed status within the given time range.

        :param started: Query jobs updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query jobs updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param statuses: Query jobs with the a specific execution status.
        :type statuses: [string]
        :param job_type_ids: Query jobs of the type associated with the identifier.
        :type job_type_ids: [int]
        :param job_type_categories: Query jobs of the type associated with the category.
        :type job_type_categories: [string]
        :param job_type_names: Query jobs of the type associated with the name.
        :type job_type_names: [string]
        :param include_superseded: Whether to include jobs that are superseded.
        :type include_superseded: bool
        :param order: A list of fields to control the sort order.
        :type order: [string]
        :returns: The list of jobs that match the time range.
        :rtype: [:class:`job.models.Job`]
        """
        if not order:
            order = ['last_status_change']
        return self.get_jobs_v5(started=started, ended=ended, statuses=statuses, job_type_ids=job_type_ids,
                                job_type_names=job_type_names, job_type_categories=job_type_categories,
                                include_superseded=include_superseded, order=order)

    def get_job_with_interfaces(self, job_id):
        """Gets the job model for the given ID with related job_type_rev and recipe__recipe_type_rev models

        :param job_id: The job ID
        :type job_id: int
        :returns: The job model with related job_type_rev and recipe__recipe_type_rev models
        :rtype: :class:`job.models.Job`
        """

        return self.select_related('job_type_rev', 'recipe__recipe_type_rev').get(id=job_id)

    def get_jobs_with_related(self, job_ids):
        """Gets the job models for the given IDs with related job_type, job_type_rev, and batch models

        :param job_ids: The job IDs
        :type job_ids: list
        :returns: The job models
        :rtype: list
        """

        return self.select_related('job_type', 'job_type_rev', 'batch').filter(id__in=job_ids)

    def get_locked_job(self, job_id):
        """Locks and returns the job model for the given ID with no related fields. Caller must be within an atomic
        transaction.

        :param job_id: The job ID
        :type job_id: int
        :returns: The job model
        :rtype: :class:`job.models.Job`
        """

        return self.get_locked_jobs([job_id])[0]

    def get_locked_jobs(self, job_ids):
        """Locks and returns the job models for the given IDs with no related fields. Caller must be within an atomic
        transaction.

        :param job_ids: The job IDs
        :type job_ids: list
        :returns: The job models
        :rtype: list
        """

        # Job models are always locked in order of ascending ID to prevent deadlocks
        return list(self.select_for_update().filter(id__in=job_ids).order_by('id').iterator())

    def increment_max_tries(self, job_ids, when):
        """Increments the max_tries of the given jobs to be their current number of executions plus the max_tries
        setting of their associated job type.

        :param job_ids: The job IDs
        :type job_ids: list
        :param when: The current time
        :type when: :class:`datetime.datetime`
        """

        if job_ids:
            qry = 'UPDATE job j SET max_tries = j.num_exes + jt.max_tries, last_modified = %s FROM job_type jt'
            qry += ' WHERE j.job_type_id = jt.id AND j.id IN %s'
            with connection.cursor() as cursor:
                cursor.execute(qry, [when, tuple(job_ids)])

    def populate_job_data_v5(self, job, data):
        #TODO remove method when v5 api is removed
        """Populates the job data and all derived fields for the given job. The caller must have obtained a model lock
        on the job model. The job should have its related job_type and job_type_rev models populated.

        :param job: The job
        :type job: :class:`job.models.Job`
        :param data: JSON description defining the job data to run on
        :type data: :class:`job.configuration.data.job_data.JobData`
        :raises job.configuration.data.exceptions.InvalidData: If the job data is invalid
        """

        # Validate job data
        interface = job.get_job_interface()
        data = JobDataSunset.create(interface, data=data.get_dict())
        interface.validate_data(data)

        # Update job model in memory
        job.input = data.get_dict()

        # Update job model in database with single query
        self.filter(id=job.id).update(input=data.get_dict())

        # Process job inputs
        self.process_job_input(job)

    def populate_input_files(self, jobs):
        """Populates each of the given jobs with its input file references in a field called "input_files".

        :param jobs: The list of jobs to augment with input files.
        :type jobs: [:class:`job.models.Job`]
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

    def process_job_input(self, job):
        """Processes the input data for the given job to populate its input file models and input meta-data fields. The
        caller must have obtained a model lock on the given job model.

        :param job: The locked job model
        :type job: :class:`job.models.Job`
        """

        if job.input_file_size is not None:
            return  # Job has already had its input processed

        # Create JobInputFile models in batches
        all_file_ids = set()
        input_file_models = []
        for file_value in job.get_input_data().values.values():
            if file_value.param_type != FileParameter.PARAM_TYPE:
                continue
            for file_id in file_value.file_ids:
                all_file_ids.add(file_id)
                job_input_file = JobInputFile()
                job_input_file.job_id = job.id
                job_input_file.input_file_id = file_id
                job_input_file.job_input = file_value.name
                input_file_models.append(job_input_file)
                if len(input_file_models) >= INPUT_FILE_BATCH_SIZE:
                    JobInputFile.objects.bulk_create(input_file_models)
                    input_file_models = []

        # Finish creating any remaining JobInputFile models
        if input_file_models:
            JobInputFile.objects.bulk_create(input_file_models)

        # Create file ancestry links for job
        from product.models import FileAncestryLink
        FileAncestryLink.objects.create_file_ancestry_links(list(all_file_ids), None, job, None)

        if len(all_file_ids) == 0:
            # If there are no input files, just zero out the file size and skip input meta-data fields
            self.filter(id=job.id).update(input_file_size=0.0)
            return

        # Set input meta-data fields on the job
        # Total input file size is in MiB rounded up to the nearest whole MiB
        qry = 'UPDATE job j SET input_file_size = CEILING(s.total_file_size / (1024.0 * 1024.0)), '
        qry += 'source_started = s.source_started, source_ended = s.source_ended, last_modified = %s, '
        qry += 'source_sensor_class = s.source_sensor_class, source_sensor = s.source_sensor, '
        qry += 'source_collection = s.source_collection, source_task = s.source_task FROM ('
        qry += 'SELECT jif.job_id, MIN(f.source_started) AS source_started, MAX(f.source_ended) AS source_ended, '
        qry += 'COALESCE(SUM(f.file_size), 0.0) AS total_file_size, '
        qry += 'MAX(f.source_sensor_class) AS source_sensor_class, '
        qry += 'MAX(f.source_sensor) AS source_sensor, '
        qry += 'MAX(f.source_collection) AS source_collection, '
        qry += 'MAX(f.source_task) AS source_task '
        qry += 'FROM scale_file f JOIN job_input_file jif ON f.id = jif.input_file_id '
        qry += 'WHERE jif.job_id = %s GROUP BY jif.job_id) s '
        qry += 'WHERE j.id = s.job_id'
        with connection.cursor() as cursor:
            cursor.execute(qry, [timezone.now(), job.id])

    def process_job_output(self, job_ids, when):
        """Processes the job output for the given job IDs. The caller must have obtained model locks on the job models
        in an atomic transaction. All jobs that are both COMPLETED and have their execution output stored, will have the
        output saved in the job model. The list of job IDs for models that are both COMPLETED and have output will be
        returned.

        :param job_ids: The job IDs
        :type job_ids: list
        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: The list of job IDs that are both COMPLETED and have output
        :rtype: list
        """

        if job_ids:
            qry = 'UPDATE job j SET output = jeo.output, last_modified = %s FROM job_exe_output jeo'
            qry += ' WHERE j.id = jeo.job_id AND j.num_exes = jeo.exe_num AND j.id IN %s AND j.status=\'COMPLETED\''
            with connection.cursor() as cursor:
                cursor.execute(qry, [when, tuple(job_ids)])

        qry = self.filter(id__in=job_ids, status='COMPLETED', jobexecutionoutput__exe_num=F('num_exes')).only('id')
        return [job.id for job in qry]

    def set_job_input_data_v6(self, job, input_data):
        """Sets the given input data as a v6 JSON for the given job. The job model must have its related job_type_rev
        model populated.

        :param job: The job model with related job_type_rev model
        :type job: :class:`job.models.Job`
        :param input_data: The input data for the job
        :type input_data: :class:`data.data.data.Data`

        :raises :class:`data.data.exceptions.InvalidData`: If the data is invalid
        """

        input_data.validate(job.job_type_rev.get_input_interface())

        if JobInterfaceSunset.is_seed_dict(job.job_type_rev.manifest):
            # Normal code path for Seed job
            input_dict = convert_data_to_v6_json(input_data).get_dict()
        else:
            # TODO: remove legacy code path when legacy job types are removed
            v1_dict = convert_data_to_v1_json(input_data, job.job_type_rev.get_input_interface()).get_dict()
            sunset_job_data = JobDataSunset.create(job.job_type_rev.manifest, v1_dict)
            if job.recipe:
                sunset_interface = JobInterfaceSunset.create(job.job_type_rev.manifest, do_validate=False)

                # Add workspace for file outputs if needed
                if sunset_interface.get_file_output_names():
                    if 'workspace_id' in job.recipe.input: # MISSING WORKSPACE IDS BECAUSE WE HAVE A V6 RECIPE!
                        workspace_id = job.recipe.input['workspace_id']
                        sunset_interface.add_workspace_to_data(sunset_job_data, workspace_id)
            input_dict = sunset_job_data.get_dict()

        self.filter(id=job.id).update(input=input_dict)

    def supersede_jobs(self, job_ids, when):
        """Updates the given job IDs to be superseded

        :param job_ids: The job IDs to supersede
        :type job_ids: list
        :param when: The time that the jobs were superseded
        :type when: :class:`datetime.datetime`
        """

        self.filter(id__in=job_ids).update(is_superseded=True, superseded=when, last_modified=timezone.now())

    # TODO: remove this when no longer needed
    def supersede_jobs_old(self, jobs, when):
        """Updates the given jobs to be superseded. The caller must have obtained model locks on the job models.

        :param jobs: The jobs to supersede
        :type jobs: [:class:`job.models.Job`]
        :param when: The time that the jobs were superseded
        :type when: :class:`datetime.datetime`
        """

        modified = timezone.now()

        # Update job models in memory and collect job IDs
        job_ids = set()
        jobs_to_cancel = []
        for job in jobs:
            job_ids.add(job.id)
            job.is_superseded = True
            job.superseded = when
            job.last_modified = modified
            if job.status in ['PENDING', 'BLOCKED']:
                jobs_to_cancel.append(job)

        # Update job models in database with single query
        self.filter(id__in=job_ids).update(is_superseded=True, superseded=when, last_modified=modified)

        # Cancel any jobs that are PENDING or BLOCKED
        if jobs_to_cancel:
            self.update_status(jobs_to_cancel, 'CANCELED', when)

    def update_jobs_node(self, job_ids, node_id, when):
        """Updates the jobs with the given IDs to have the given node and start time

        :param job_ids: A list of job IDs to update
        :type job_ids: list
        :param node_id: The node ID
        :type node_id: int
        :param when: The start time
        :type when: :class:`datetime.datetime`
        """

        self.filter(id__in=job_ids).update(node_id=node_id, started=when, last_modified=timezone.now())

    def update_jobs_to_blocked(self, jobs, when):
        """Updates the given job models to the BLOCKED status and returns the IDs of the models that were successfully
        set to BLOCKED. The caller must have obtained model locks on the job models in an atomic transaction. Any jobs
        that are not in a valid state for being BLOCKED will be ignored.

        :param jobs: The job models to set to BLOCKED
        :type jobs: list
        :param when: The status change time
        :type when: :class:`datetime.datetime`
        :returns: The list of job IDs that were successfully set to BLOCKED
        :rtype: list
        """

        job_ids = []
        for job in jobs:
            if job.can_be_blocked():
                job_ids.append(job.id)

        self.filter(id__in=job_ids).update(status='BLOCKED', last_status_change=when, last_modified=timezone.now())
        return job_ids

    def update_jobs_to_canceled(self, jobs, when):
        """Updates the given job models to the CANCELED status and returns the IDs of the models that were successfully
        set to CANCELED. The caller must have obtained model locks on the job models in an atomic transaction. Any jobs
        that are not in a valid state for being CANCELED will be ignored.

        :param jobs: The job models to set to CANCELED
        :type jobs: list
        :param when: The status change time
        :type when: :class:`datetime.datetime`
        :returns: The list of job IDs that were successfully set to CANCELED
        :rtype: list
        """

        job_ids = []
        for job in jobs:
            if job.can_be_canceled():
                job_ids.append(job.id)

        self.filter(id__in=job_ids).update(status='CANCELED', error=None, node=None, last_status_change=when,
                                           last_modified=timezone.now())
        return job_ids

    # TODO: remove once REST API v5 is removed
    @transaction.atomic
    def update_jobs_to_canceled_old(self, job_ids, when):
        """Updates the given jobs to the CANCELED status. Any jobs that cannot be canceled will be ignored. All database
        updates occur in an atomic transaction.

        :param job_ids: The list of job IDs
        :type job_ids: list
        :param when: The cancel time
        :type when: :class:`datetime.datetime`
        """

        jobs_to_update = []
        for locked_job in self.get_locked_jobs(job_ids):
            if locked_job.status not in ['COMPLETED', 'CANCELED']:
                jobs_to_update.append(locked_job.id)

        if jobs_to_update:
            # Update job models in database
            self.filter(id__in=jobs_to_update).update(status='CANCELED', error=None, node=None, last_status_change=when,
                                                      last_modified=timezone.now())

    def update_jobs_to_completed(self, jobs, when):
        """Updates the given job models to the COMPLETED status and returns the IDs of the models that were successfully
        set to COMPLETED. The caller must have obtained model locks on the job models in an atomic transaction. Any jobs
        that are not in a valid state for being COMPLETED will be ignored.

        :param jobs: The job models to set to COMPLETED
        :type jobs: list
        :param when: The ended time
        :type when: :class:`datetime.datetime`
        :returns: The list of job IDs that were successfully set to COMPLETED
        :rtype: list
        """

        job_ids = []
        for job in jobs:
            if job.can_be_completed():
                job_ids.append(job.id)

        self.filter(id__in=job_ids).update(status='COMPLETED', ended=when, last_status_change=when,
                                           last_modified=timezone.now())
        return job_ids

    def update_jobs_to_failed(self, jobs, error_id, when):
        """Updates the given job models to the FAILED status and returns the IDs of the models that were successfully
        set to FAILED. The caller must have obtained model locks on the job models in an atomic transaction. Any jobs
        that are not in a valid state for being FAILED will be ignored.

        :param jobs: The job models to set to FAILED
        :type jobs: list
        :param error_id: The ID of the error that caused the failure
        :type error_id: int
        :param when: The ended time
        :type when: :class:`datetime.datetime`
        :returns: The list of job IDs that were successfully set to FAILED
        :rtype: list
        """

        job_ids = []
        for job in jobs:
            if job.can_be_failed():
                job_ids.append(job.id)

        self.filter(id__in=job_ids).update(status='FAILED', error_id=error_id, ended=when, last_status_change=when,
                                           last_modified=timezone.now())
        return job_ids

    def update_jobs_to_pending(self, jobs, when):
        """Updates the given job models to the PENDING status and returns the IDs of the models that were successfully
        set to PENDING. The caller must have obtained model locks on the job models in an atomic transaction. Any jobs
        that are not in a valid state for being PENDING will be ignored.

        :param jobs: The job models to set to PENDING
        :type jobs: list
        :param when: The status change time
        :type when: :class:`datetime.datetime`
        :returns: The list of job IDs that were successfully set to PENDING
        :rtype: list
        """

        job_ids = []
        for job in jobs:
            if job.can_be_pending():
                job_ids.append(job.id)

        self.filter(id__in=job_ids).update(status='PENDING', last_status_change=when, last_modified=timezone.now())
        return job_ids

    def update_jobs_to_queued(self, jobs, when_queued, requeue=False):
        """Updates the given job models to the QUEUED status and returns the IDs of the models that were successfully
        set to QUEUED. The caller must have obtained model locks on the job models in an atomic transaction. Any jobs
        that are not in a valid status for being queued, are without job input, or are superseded will be ignored.

        :param jobs: The job models to set to QUEUED
        :type jobs: list
        :param when_queued: The time that the jobs are queued
        :type when_queued: :class:`datetime.datetime`
        :param requeue: Whether this is a re-queue (True) or a first queue (False)
        :type requeue: bool
        :returns: The list of job IDs that were successfully set to QUEUED
        :rtype: list
        """

        job_ids = []
        for job in jobs:
            if requeue:
                if job.can_be_requeued():
                    job_ids.append(job.id)
            else:
                if job.can_be_queued():
                    job_ids.append(job.id)

        self.filter(id__in=job_ids).update(status='QUEUED', node=None, error=None, queued=when_queued, started=None,
                                           ended=None, last_status_change=when_queued,
                                           num_exes=models.F('num_exes') + 1, last_modified=timezone.now())
        return job_ids

    def update_jobs_to_running(self, jobs, when):
        """Updates the given job models to the RUNNING status and returns the IDs of the models that were successfully
        set to RUNNING. The caller must have obtained model locks on the job models in an atomic transaction. Any jobs
        that are not in a valid state for RUNNING will be ignored.

        :param jobs: The job models to set to RUNNING
        :type jobs: list
        :param when: The start time
        :type when: :class:`datetime.datetime`
        :returns: The list of job IDs that were successfully set to RUNNING
        :rtype: list
        """

        job_ids = []
        for job in jobs:
            if job.can_be_running():
                job_ids.append(job.id)

        self.filter(id__in=job_ids).update(status='RUNNING', last_status_change=when, last_modified=timezone.now())
        return job_ids

    # TODO: this needs to be removed as usage of this is refactored into the messaging backend
    def update_status(self, jobs, status, when, error=None):
        """Updates the given jobs with the new status. The caller must have obtained model locks on the job models.

        :param jobs: The jobs to update
        :type jobs: [:class:`job.models.Job`]
        :param status: The new status
        :type status: string
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

    # TODO: remove this function when API REST v5 is removed
    def _merge_job_data(self, job_interface_dict, job_data_dict, job_files):
        """Merges data for a single job instance with its job interface to produce a mapping of key/values.

        :param job_interface_dict: A dictionary representation of the job type interface.
        :type job_interface_dict: dict
        :param job_data_dict: A dictionary representation of the job instance data.
        :type job_data_dict: dict
        :param job_files: A list of files that are referenced by the job data.
        :type job_files: [:class:`storage.models.ScaleFile`]
        :return: A dictionary of each interface key mapped to the corresponding data value.
        :rtype: dict
        """

        # Setup the basic structure for merged results
        merged_dicts = copy.deepcopy(job_interface_dict)
        name_map = {merged_dict['name']: merged_dict for merged_dict in merged_dicts}
        file_map = {job_file.id: job_file for job_file in job_files}

        # Merge the job data with the interface attributes
        for data_dict in job_data_dict:
            value = None
            if 'value' in data_dict:
                value = data_dict['value']
            elif 'file_id' in data_dict:
                value = file_map[data_dict['file_id']]
            elif 'file_ids' in data_dict:
                value = [file_map[file_id] for file_id in data_dict['file_ids']]

            name = data_dict['name']
            if name in name_map:
                merged_dict = name_map[name]
                merged_dict['value'] = value
        return merged_dicts


class Job(models.Model):
    """Represents a job to be run on the cluster. A model lock must be obtained using select_for_update() on any job
    model before updating its status or superseding it.

    :keyword job_type: The type of this job
    :type job_type: :class:`django.db.models.ForeignKey`
    :keyword job_type_rev: The revision of the job type when this job was created
    :type job_type_rev: :class:`django.db.models.ForeignKey`
    :keyword event: The event that triggered the creation of this job
    :type event: :class:`django.db.models.ForeignKey`
    :keyword ingest_event: The ingest event that triggered the creation of this job
    :type ingest_event: :class:`django.db.models.ForeignKey`
    :keyword root_recipe: The root recipe that contains this job
    :type root_recipe: :class:`django.db.models.ForeignKey`
    :keyword recipe: The original recipe that created this job
    :type recipe: :class:`django.db.models.ForeignKey`
    :keyword batch: The batch that contains this job
    :type batch: :class:`django.db.models.ForeignKey`

    :keyword is_superseded: Whether this job has been superseded and is obsolete. This may be true while
        superseded_by_job (the reverse relationship of superseded_job) is null, indicating that this job is obsolete
        (its recipe has been superseded), but there is no new job that has directly taken its place.
    :type is_superseded: :class:`django.db.models.BooleanField`
    :keyword root_superseded_job: The first job in the chain of superseded jobs. This field will be null for the first
        job in the chain (i.e. jobs that have a null superseded_job field).
    :type root_superseded_job: :class:`django.db.models.ForeignKey`
    :keyword superseded_job: The job that was directly superseded by this job. The reverse relationship can be accessed
        using 'superseded_by_job'.
    :type superseded_job: :class:`django.db.models.ForeignKey`
    :keyword delete_superseded: Whether this job should delete the products of the job that it has directly superseded
    :type delete_superseded: :class:`django.db.models.BooleanField`

    :keyword status: The status of the job
    :type status: :class:`django.db.models.CharField`
    :keyword node: The node on which the job is/was running (should only be set if status is RUNNING or final status)
    :type node: :class:`django.db.models.ForeignKey`
    :keyword error: The error that caused the failure (should only be set when status is FAILED)
    :type error: :class:`django.db.models.ForeignKey`
    :keyword max_tries: The maximum number of times to try executing this job in case of errors (minimum one)
    :type max_tries: :class:`django.db.models.IntegerField`
    :keyword num_exes: The number of executions this job has had
    :type num_exes: :class:`django.db.models.IntegerField`

    :keyword priority: The priority of the job (lower number is higher priority)
    :type priority: :class:`django.db.models.IntegerField`
    :keyword timeout: The maximum amount of time to allow this job to run before being killed (in seconds)
    :type timeout: :class:`django.db.models.IntegerField`
    :keyword input: JSON description defining the data for this job. This field must be populated when the job is first
        queued.
    :type input: :class:`django.contrib.postgres.fields.JSONField`
    :keyword input_file_size: The amount of disk space in MiB required for input files for this job
    :type input_file_size: :class:`django.db.models.FloatField`
    :keyword output: JSON description defining the results for this job. This field is populated when the job is
        successfully completed.
    :type output: :class:`django.contrib.postgres.fields.JSONField`
    :keyword configuration: JSON describing the overriding job configuration for this job instance
    :type configuration: :class:`django.contrib.postgres.fields.JSONField`

    :keyword source_started: The start time of the source data for this job
    :type source_started: :class:`django.db.models.DateTimeField`
    :keyword source_ended: The end time of the source data for this job
    :type source_ended: :class:`django.db.models.DateTimeField`
    :keyword source_sensor_class: The class of sensor used to produce the source file for this job
    :type source_sensor_class: :class:`django.db.models.CharField`
    :keyword source_sensor: The specific identifier of the sensor used to produce the source file for this job
    :type source_sensor: :class:`django.db.models.CharField`
    :keyword source_collection: The collection of the source file for this job
    :type source_collection: :class:`django.db.models.CharField`
    :keyword source_task: The task that produced the source file for this job
    :type source_task: :class:`django.db.models.CharField`

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
    event = models.ForeignKey('trigger.TriggerEvent', blank=True, null=True, on_delete=models.PROTECT)
    ingest_event = models.ForeignKey('ingest.IngestEvent', blank=True, null=True, on_delete=models.PROTECT)
    root_recipe = models.ForeignKey('recipe.Recipe', related_name='jobs_for_root_recipe', blank=True, null=True,
                                    on_delete=models.PROTECT)
    recipe = models.ForeignKey('recipe.Recipe', related_name='jobs_for_recipe', blank=True, null=True,
                               on_delete=models.PROTECT)
    batch = models.ForeignKey('batch.Batch', related_name='jobs_for_batch', blank=True, null=True,
                              on_delete=models.PROTECT)

    is_superseded = models.BooleanField(default=False)
    root_superseded_job = models.ForeignKey('job.Job', related_name='superseded_by_jobs', blank=True, null=True,
                                            on_delete=models.PROTECT)
    superseded_job = models.OneToOneField('job.Job', related_name='superseded_by_job', blank=True, null=True,
                                          on_delete=models.PROTECT)
    delete_superseded = models.BooleanField(default=True)

    status = models.CharField(choices=JOB_STATUSES, default='PENDING', max_length=50, db_index=True)
    node = models.ForeignKey('node.Node', blank=True, null=True, on_delete=models.PROTECT)
    error = models.ForeignKey('error.Error', blank=True, null=True, on_delete=models.PROTECT)
    max_tries = models.IntegerField()
    num_exes = models.IntegerField(default=0)

    # TODO: priority and timeout can be removed when legacy job types are removed
    priority = models.IntegerField(null=True)
    timeout = models.IntegerField(null=True)

    input = django.contrib.postgres.fields.JSONField(blank=True, null=True)
    input_file_size = models.FloatField(blank=True, null=True)
    output = django.contrib.postgres.fields.JSONField(blank=True, null=True)
    configuration = django.contrib.postgres.fields.JSONField(blank=True, null=True)

    # Supplemental sensor metadata fields
    source_started = models.DateTimeField(blank=True, null=True, db_index=True)
    source_ended = models.DateTimeField(blank=True, null=True, db_index=True)
    source_sensor_class = models.TextField(blank=True, null=True, db_index=True)
    source_sensor = models.TextField(blank=True, null=True, db_index=True)
    source_collection = models.TextField(blank=True, null=True, db_index=True)
    source_task = models.TextField(blank=True, null=True, db_index=True)


    created = models.DateTimeField(auto_now_add=True)
    queued = models.DateTimeField(blank=True, null=True)
    started = models.DateTimeField(blank=True, null=True)
    ended = models.DateTimeField(blank=True, null=True)
    last_status_change = models.DateTimeField(blank=True, db_index=True, null=True)
    superseded = models.DateTimeField(blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = JobManager()

    def can_be_blocked(self):
        """Indicates whether this job can be set to BLOCKED status

        :returns: True if the job can be set to BLOCKED status, false otherwise
        :rtype: bool
        """

        return self.status != 'BLOCKED' and not self.has_been_queued()

    def can_be_canceled(self):
        """Indicates whether this job can be set to CANCELED status

        :returns: True if the job can be set to CANCELED status, false otherwise
        :rtype: bool
        """

        return self.status not in ['CANCELED', 'COMPLETED']

    def can_be_completed(self):
        """Indicates whether this job can be set to COMPLETED status

        :returns: True if the job can be set to COMPLETED status, false otherwise
        :rtype: bool
        """

        # QUEUED is allowed because the RUNNING update may come after the completion
        return self.status in ['QUEUED', 'RUNNING']

    def can_be_failed(self):
        """Indicates whether this job can be set to FAILED status

        :returns: True if the job can be set to FAILED status, false otherwise
        :rtype: bool
        """

        # QUEUED is allowed because the RUNNING update may come after the failure
        return self.status in ['QUEUED', 'RUNNING']

    def can_be_pending(self):
        """Indicates whether this job can be set to PENDING status

        :returns: True if the job can be set to PENDING status, false otherwise
        :rtype: bool
        """

        return self.status != 'PENDING' and not self.has_been_queued()

    def can_be_queued(self):
        """Indicates whether this job can be placed on the queue for the first time

        :returns: True if the job can be placed on the queue for the first time, false otherwise
        :rtype: bool
        """

        first_time = not self.has_been_queued()
        return self.status in ['PENDING', 'BLOCKED'] and self.has_input() and first_time and not self.is_superseded

    def can_be_requeued(self):
        """Indicates whether this job can be placed back on the queue (re-queued)

        :returns: True if the job can be placed back on the queue, false otherwise
        :rtype: bool
        """

        # QUEUED is allowed because the RUNNING update may come after the failure
        return self.status != 'COMPLETED' and self.has_input() and self.has_been_queued() and not self.is_superseded

    def can_be_running(self):
        """Indicates whether this job can be set to RUNNING status

        :returns: True if the job can be set to RUNNING status, false otherwise
        :rtype: bool
        """

        return self.status == 'QUEUED'

    def can_be_uncanceled(self):
        """Indicates whether this job can be uncanceled. Jobs can be uncanceled if they are currently canceled and have
        never been queued before.

        :returns: True if the job can be uncanceled, false otherwise
        :rtype: bool
        """

        return self.status == 'CANCELED' and not self.has_been_queued()

    def get_job_configuration(self):
        """Returns the job configuration for this job

        :returns: The job configuration for this job
        :rtype: :class:`job.configuration.configuration.JobConfiguration`
        """

        if self.configuration:
            return JobConfigurationV6(config=self.configuration, do_validate=False).get_configuration()
        else:
            return self.job_type.get_job_configuration()

    def get_v6_configuration_json(self):
        """Returns the job configuration in v6 of the JSON schema

        :returns: The job configuration in v6 of the JSON schema
        :rtype: dict
        """

        if self.configuration:
            return rest_utils.strip_schema_version(convert_config_to_v6_json(self.get_job_configuration()).get_dict())
        else:
            return None

    def get_input_data(self):
        """Returns the input data for this job

        :returns: The input data for this job
        :rtype: :class:`data.data.data.Data`
        """

        return DataV6(data=self.input, do_validate=False).get_data()

    def get_v6_input_data_json(self):
        """Returns the input data for this job as v6 json with the version stripped

        :returns: The v6 JSON input data dict for this job
        :rtype: dict
        """

        return rest_utils.strip_schema_version(convert_data_to_v6_json(self.get_input_data()).get_dict())

    # TODO: deprecated in favor of get_input_data(), remove this when all uses of it have been removed
    def get_job_data(self):
        """Returns the data for this job

        :returns: The data for this job
        :rtype: :class:`job.configuration.data.job_data.JobData` or :class:`job.data.job_data.JobData`
        """

        # TODO: Remove old JobData in v6 when we transition to only Seed job types
        if self.input and 'version' in self.input and '6' == self.input['version']:
            job_data = JobData(self.input)
        else:
            # Handle self.input being none on Seed type jobs
            if JobInterfaceSunset.is_seed_dict(self.job_type_rev.manifest):
                job_data = JobData(self.input)
            else:
                job_data = JobData_1_0(self.input)
        return job_data

    def get_job_interface(self):
        """Returns the interface for this job

        :returns: The interface for this job
        :rtype: :class:`job.configuration.interface.job_interface.JobInterface` or :class:`job.seed.manifest.SeedManifest`
        """

        return JobInterfaceSunset.create(self.job_type_rev.manifest)

    def get_job_results(self):
        """Returns the results for this job

        :returns: The results for this job
        :rtype: :class:`job.configuration.results.job_results.JobResults` or
                :class:`job.seed.results.job_results.JobResults`
        """

        # TODO: Remove old JobResults in v6 when we transition to only Seed job types
        if self.output and 'version' in self.output and '6' == self.output['version']:
            job_results = JobResults(self.output)
        else:
            # Handle self.output being none on Seed type jobs
            if JobInterfaceSunset.is_seed_dict(self.job_type_rev.manifest):
                job_results = JobResults(self.output)
            else:
                job_results = JobResults_1_0(self.output)
        return job_results

    def get_output_data(self):
        """Returns the output data for this job

        :returns: The output data for this job
        :rtype: :class:`data.data.data.Data`
        """

        return DataV6(data=self.output, do_validate=False).get_data()

    def get_v6_output_data_json(self):
        """Returns the output data for this job as v6 json with the version stripped

        :returns: The v6 JSON output data dict for this job
        :rtype: dict
        """

        return rest_utils.strip_schema_version(convert_data_to_v6_json(self.get_output_data()).get_dict())

    def get_resources(self):
        """Returns the resources required for this job

        :returns: The required resources
        :rtype: :class:`node.resources.node_resources.NodeResources`
        """

        resources = self.job_type.get_resources()

        # Input File Size in MiB
        input_file_size = self.input_file_size
        if not input_file_size:
            input_file_size = 0.0

        interface = self.job_type.get_job_interface()

        # TODO: remove legacy code branch in v6
        if not isinstance(interface, SeedManifest):
            # Calculate memory required in MiB rounded up to the nearest whole MiB
            multiplier = self.job_type.mem_mult_required
            const = self.job_type.mem_const_required

            memory_mb = long(math.ceil(multiplier * input_file_size + const))
            memory_required = max(memory_mb, MIN_MEM)

            # Calculate output space required in MiB rounded up to the nearest whole MiB
            multiplier = self.job_type.disk_out_mult_required
            const = self.job_type.disk_out_const_required
            output_size_mb = long(math.ceil(multiplier * input_file_size + const))
            disk_out_required = max(output_size_mb, MIN_DISK)

            resources.add(NodeResources([Mem(memory_required), Disk(disk_out_required + input_file_size)]))
        # TODO: Seed logic block to keep in v6
        else:
            scalar_resources = []
            # Iterate over all scalar resources and
            for resource in interface.get_scalar_resources():
                if 'inputMultiplier' in resource:
                    multiplier = resource['inputMultiplier']
                    initial_value = long(math.ceil(multiplier * input_file_size + resource['value']))
                    value_required = max(initial_value, MIN_RESOURCE.get(resource['name'], 0.0))
                    scalar_resources.append(ScalarResource(resource['name'], value_required))

            if scalar_resources:
                resources.increase_up_to(NodeResources(scalar_resources))

            # We have to ensure shared memory is not a required NodeResource, otherwise scheduling cannot occur
            resources.remove_resource('sharedmem')

            # If no inputMultiplier for Disk we need to at least ensure it exceeds input_file_size
            resources.increase_up_to(NodeResources([Disk(input_file_size)]))

        return resources

    def get_resources_dict(self):
        """Gathers resources information and returns it as a dict.

        :returns: The job resources dict
        :rtype: dict
        """

        return self.get_resources().get_json().get_dict()

    def get_v6_resources_json(self):
        """Returns the job resources in v6 of the JSON schema

        :returns: The job resources in v6 of the JSON schema
        :rtype: dict
        """

        return rest_utils.strip_schema_version(self.get_resources_dict())

    def has_been_queued(self):
        """Indicates whether this job has been queued at least once

        :returns: True if the job has been queued at least once, false otherwise.
        :rtype: bool
        """

        return self.num_exes > 0

    def has_input(self):
        """Indicates whether this job has its input

        :returns: True if the job has its input, false otherwise.
        :rtype: bool
        """

        return True if self.input else False

    def has_output(self):
        """Indicates whether this job has its output

        :returns: True if the job has its output, false otherwise.
        :rtype: bool
        """

        return True if self.output else False

    def is_ready_for_children(self):
        """Indicates whether this job is ready for its children jobs to be queued

        :returns: True if this job is ready for its children jobs, false otherwise
        :rtype: bool
        """

        return self.status == 'COMPLETED' and self.has_output()

    def set_input(self, job_input):
        """Validates and sets the input for this job model. No database update is applied. This job should have its
        related job_type and job_type_rev models populated.

        :param job_input: JSON description defining the job input
        :type job_input: :class:`job.configuration.data.job_data.JobData`
        :raises job.configuration.data.exceptions.InvalidData: If the job input is invalid
        """

        interface = self.get_job_interface()
        interface.validate_data(job_input)
        self.input = job_input.get_dict()

    def update_database_with_input(self, when):
        """Updates the database with this job's input JSON

        :param when: The current time
        :type when: :class:`datetime.datetime`
        """

        Job.objects.filter(id=self.id).update(input=self.input, last_modified=when)

    # TODO: remove when REST API v5 is removed
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

    # TODO: remove when REST API v5 is removed
    def get_details(self, job_exe_id):
        """Gets additional details for the given job execution model based on related model attributes.

        :param job_exe_id: The unique identifier of the job execution.
        :type job_exe_id: int
        :returns: The job execution with extra related attributes.
        :rtype: :class:`job.models.JobExecution`
        """

        job_exe = JobExecution.objects.all().select_related(
            'job', 'job__job_type', 'job__error', 'job__event', 'job__event__rule', 'node', 'error', 'jobexecutionend',
            'jobexecutionoutput'
        )
        job_exe = job_exe.defer('stdout', 'stderr')
        job_exe = job_exe.get(pk=job_exe_id)

        # Populate command arguments
        job_exe.command_arguments = job_exe.get_execution_configuration().get_args('main')

        # Populate resource fields
        resources = job_exe.get_resources()
        job_exe.cpus_scheduled = resources.cpus
        job_exe.mem_scheduled = resources.mem
        job_exe.disk_total_scheduled = resources.disk
        job_exe.disk_out_scheduled = job_exe.disk_total_scheduled - job_exe.input_file_size

        # Populate old task fields with data from task results JSON
        try:
            if job_exe.jobexecutionend:
                for task_dict in job_exe.jobexecutionend.get_task_results().get_dict()['tasks']:
                    if 'was_started' in task_dict and task_dict['was_started']:
                        if task_dict['type'] == 'pre':
                            job_exe.pre_started = dateparse.parse_datetime(task_dict['started'])
                            job_exe.pre_completed = dateparse.parse_datetime(task_dict['ended'])
                            job_exe.pre_exit_code = task_dict['exit_code']
                        elif task_dict['type'] == 'main':
                            job_exe.job_started = dateparse.parse_datetime(task_dict['started'])
                            job_exe.job_completed = dateparse.parse_datetime(task_dict['ended'])
                            job_exe.job_exit_code = task_dict['exit_code']
                        elif task_dict['type'] == 'post':
                            job_exe.post_started = dateparse.parse_datetime(task_dict['started'])
                            job_exe.post_completed = dateparse.parse_datetime(task_dict['ended'])
                            job_exe.post_exit_code = task_dict['exit_code']
        except JobExecutionEnd.DoesNotExist:
            pass

        return job_exe

    # TODO: remove when REST API v5 is removed
    def get_exes(self, started=None, ended=None, statuses=None, job_type_ids=None, job_type_names=None,
                 job_type_categories=None, node_ids=None, order=None):
        """Returns a list of job executions within the given time range.

        :param started: Query job executions updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query job executions updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param statuses: Query job executions with the a specific status.
        :type statuses: [string]
        :param job_type_ids: Query job executions of the type associated with the identifier.
        :type job_type_ids: [int]
        :param job_type_names: Query job executions of the type associated with the name.
        :type job_type_names: [string]
        :param job_type_categories: Query job executions of the type associated with the category.
        :type job_type_categories: [string]
        :param node_ids: Query job executions that ran on a node with the identifier.
        :type node_ids: [int]
        :param order: A list of fields to control the sort order.
        :type order: [string]
        :returns: The list of job executions that match the time range.
        :rtype: [:class:`job.models.JobExecution`]
        """

        # Fetch a list of job executions
        job_exes = JobExecution.objects.all().select_related('job', 'job_type', 'node', 'jobexecutionend__error',
                                                             'jobexecutionoutput')
        job_exes = job_exes.defer('stdout', 'stderr')

        # Apply time range filtering
        if started:
            job_exes = job_exes.filter(last_modified__gte=started)
        if ended:
            job_exes = job_exes.filter(last_modified__lte=ended)

        if statuses:
            if 'RUNNING' in statuses:
                # This is a special case where we have to use exclusion so that running executions (no job_exe_end) are
                # included
                exclude_statues = []
                for status in ['COMPLETED', 'FAILED', 'CANCELED']:
                    if status not in statuses:
                        exclude_statues.append(status)
                job_exes = job_exes.exclude(jobexecutionend__status__in=exclude_statues)
            else:
                job_exes = job_exes.filter(jobexecutionend__status__in=statuses)
        if job_type_ids:
            job_exes = job_exes.filter(job_type_id__in=job_type_ids)
        if job_type_names:
            job_exes = job_exes.filter(job_type__name__in=job_type_names)
        if job_type_categories:
            job_exes = job_exes.filter(job_type__category__in=job_type_categories)
        if node_ids:
            job_exes = job_exes.filter(node_id__in=node_ids)

        # Apply sorting
        if order:
            job_exes = job_exes.order_by(*order)
        else:
            job_exes = job_exes.order_by('created')
        return job_exes

    def get_job_exes(self, job_id, started=None, ended=None, statuses=None, node_ids=None, error_ids=None,
                     error_categories=None, order=None):
        """Returns a list of job executions for the given job.

        :param job_id: Query job executions associated with the job identifier.
        :type job_id: int
        :param started: Query job executions updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query job executions updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param statuses: Query job executions with the a specific status.
        :type statuses: [string]
        :param node_ids: Query job executions that ran on a node with the identifier.
        :type node_ids: [int]
        :param error_ids: Query job executions that had an error with the identifier.
        :type error_ids: [int]
        :param error_categories: Query job executions that had an error with the given category.
        :type error_categories: [string]
        :param order: A list of fields to control the sort order.
        :type order: [string]
        :returns: The list of job executions that match the job identifier.
        :rtype: [:class:`job.models.JobExecution`]
        """

        # Fetch a list of job executions
        job_exes = JobExecution.objects.all().select_related('job', 'job_type', 'node', 'jobexecutionend',
                                                             'jobexecutionend__error')
        job_exes = job_exes.defer('stdout', 'stderr')

        # Apply job filtering
        job_exes = job_exes.filter(job__id=job_id)

        # Apply time range filtering
        if started:
            job_exes = job_exes.filter(started__gte=started)
        if ended:
            job_exes = job_exes.filter(jobexecutionend__ended__lte=ended)

        # Apply status and node filtering
        if statuses:
            if 'RUNNING' in statuses:
                # This is a special case where we have to use exclusion so that running executions (no job_exe_end) are
                # included
                exclude_statues = []
                for status in ['COMPLETED', 'FAILED', 'CANCELED']:
                    if status not in statuses:
                        exclude_statues.append(status)
                job_exes = job_exes.exclude(jobexecutionend__status__in=exclude_statues)
            else:
                job_exes = job_exes.filter(jobexecutionend__status__in=statuses)
        if node_ids:
            job_exes = job_exes.filter(node_id__in=node_ids)
        if error_ids:
            job_exes = job_exes.filter(jobexecutionend__error_id__in=error_ids)
        if error_categories:
            job_exes = job_exes.filter(jobexecutionend__error__category__in=error_categories)

        # Apply sorting
        if order:
            job_exes = job_exes.order_by(*order)
        else:
            job_exes = job_exes.order_by('-exe_num')

        return job_exes

    def get_job_exe_details(self, job_id, exe_num):
        """Returns additional details about a job execution related to the given job identifier and execution number.

        :param job_id: Query job executions associated with the job identifier.
        :type job_id: int
        :param exe_num: Query job executions associated with the execution number.
        :type exe_num: int
        :returns: Details about the job execution that match the job execution identifier.
        :rtype: [:class:`job.models.JobExecution`]
        """

        # Fetch a list of job executions
        job_exe = JobExecution.objects.all().select_related('job', 'job_type', 'node', 'jobexecutionend',
                                                            'jobexecutionend__error', 'jobexecutionoutput')
        job_exe = job_exe.defer('stdout', 'stderr', 'job__input', 'job__output')

        # Apply job and execution filtering
        job_exe = job_exe.get(job__id=job_id, exe_num=exe_num)

        return job_exe

    def get_job_exe_with_job_and_job_type(self, job_id, exe_num):
        """Gets a job execution with its related job and job_type models populated using only one database query

        :param job_id: The job ID
        :type job_id: int
        :param exe_num: The execution number
        :type exe_num: int
        :returns: The job execution model with related job and job_type models populated
        :rtype: :class:`job.models.JobExecution`
        """

        try:
            return self.select_related('job__job_type', 'job__job_type_rev').get(job_id=job_id, exe_num=exe_num)
        except JobExecution.DoesNotExist:
            pass

        logger.warning('Job execution with number %d not found, querying for last job execution', exe_num)
        job_exe = self.select_related('job__job_type', 'job__job_type_rev').filter(job_id=job_id).order('-id')[0]
        logger.info('Found job execution with ID %d', job_exe.id)
        return job_exe

    # TODO: remove when REST API v5 is removed
    def get_latest(self, jobs):
        """Gets the latest job execution associated with each given job.

        :param jobs: The jobs to populate with latest execution models.
        :type jobs: [class:`job.models.Job`]
        :returns: A dictionary that maps each job identifier to its latest execution.
        :rtype: dict of int -> class:`job.models.JobExecution`
        """
        job_exes = JobExecution.objects.filter(job__in=jobs).defer('stdout', 'stderr')

        results = {}
        for job_exe in job_exes:
            if job_exe.job_id not in results or job_exe.created > results[job_exe.job_id].created:
                results[job_exe.job_id] = job_exe

        return results

    def get_latest_execution(self, job_id):
        """Gets the latest job execution for the given job ID and returns it with the related job model

        :param job_id: The job ID
        :type job_id: int
        :returns: The job execution model with related job and job_type models populated
        :rtype: :class:`job.models.JobExecution`
        """

        return self.select_related('job').get(job_id=job_id, exe_num=F('job__num_exes'))

    # TODO: remove when REST API v5 is removed
    def get_logs(self, job_exe_id):
        """Gets additional details for the given job execution model based on related model attributes.

        :param job_exe_id: The unique identifier of the job execution.
        :type job_exe_id: int
        :returns: The job execution with extra related attributes.
        :rtype: :class:`job.models.JobExecution`
        """
        job_exe = JobExecution.objects.all().select_related('job', 'job__job_type', 'node', 'error')
        job_exe = job_exe.get(pk=job_exe_id)

        return job_exe

    def get_unfinished_job_exes(self):
        """Returns the job executions for the jobs that are unfinished. Unfinished jobs are jobs where the latest
        execution has been scheduled, but the job is still in QUEUED or RUNNING status. The returned job executions will
        not have any of their JSON fields populated. The returned list is a queryset iterator, so only access it once.

        :returns: The job execution models for the unfinished jobs
        :rtype: list
        """

        qry = self.filter(job__status__in=['QUEUED', 'RUNNING'], exe_num=F('job__num_exes'))
        qry = qry.defer('resources', 'configuration').iterator()
        return qry


class JobExecution(models.Model):
    """Represents a job execution that has been scheduled to run on a node

    :keyword job: The job that was scheduled
    :type job: :class:`django.db.models.ForeignKey`
    :keyword job_type: The type of the job that was scheduled
    :type job_type: :class:`django.db.models.ForeignKey`
    :keyword recipe: The original recipe that created this job
    :type recipe: :class:`django.db.models.ForeignKey`
    :keyword batch: The batch that contains this job
    :type batch: :class:`django.db.models.ForeignKey`
    :keyword exe_num: The number of the job's execution
    :type exe_num: :class:`django.db.models.IntegerField`
    :keyword cluster_id: This is an ID for the job execution that is unique in the context of the cluster, allowing
        Scale components (task IDs, Docker volume names, etc) to have unique names within the cluster
    :type cluster_id: :class:`django.db.models.CharField`
    :keyword node: The node on which the job execution is scheduled
    :type node: :class:`django.db.models.ForeignKey`

    :keyword timeout: The maximum amount of time to allow this execution to run before being killed (in seconds)
    :type timeout: :class:`django.db.models.IntegerField`
    :keyword input_file_size: The total amount of disk space in MiB for all input files for this job execution
    :type input_file_size: :class:`django.db.models.FloatField`
    :keyword resources: JSON description describing the resources allocated to this job execution
    :type resources: :class:`django.contrib.postgres.fields.JSONField`
    :keyword configuration: JSON description describing the configuration for how the job execution should be run
    :type configuration: :class:`django.contrib.postgres.fields.JSONField`

    :keyword queued: When the job execution was added to the queue
    :type queued: :class:`django.db.models.DateTimeField`
    :keyword started: When the job execution was started (scheduled)
    :type started: :class:`django.db.models.DateTimeField`
    :keyword created: When this model was created
    :type created: :class:`django.db.models.DateTimeField`
    """

    job = models.ForeignKey('job.Job', on_delete=models.PROTECT)
    job_type = models.ForeignKey('job.JobType', blank=True, null=True, on_delete=models.PROTECT)
    recipe = models.ForeignKey('recipe.Recipe', blank=True, null=True, on_delete=models.PROTECT)
    batch = models.ForeignKey('batch.Batch', blank=True, null=True, on_delete=models.PROTECT)
    exe_num = models.IntegerField(blank=True, null=True)
    cluster_id = models.CharField(blank=True, max_length=100, null=True)
    node = models.ForeignKey('node.Node', blank=True, null=True, on_delete=models.PROTECT)
    docker_image = models.TextField(null=True)

    timeout = models.IntegerField()
    input_file_size = models.FloatField(blank=True, null=True)
    resources = django.contrib.postgres.fields.JSONField(default=dict)
    configuration = django.contrib.postgres.fields.JSONField(default=dict)

    queued = models.DateTimeField()
    started = models.DateTimeField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    # TODO: old fields that are being nulled out, they should be removed in the future after they have been moved to the
    # new job_exe_end and job_exe_output tables and they are no longer needed for the REST API
    status = models.CharField(blank=True, max_length=50, null=True, db_index=True)
    error = models.ForeignKey('error.Error', blank=True, null=True, on_delete=models.PROTECT)
    command_arguments = models.CharField(blank=True, max_length=1000, null=True)
    environment = django.contrib.postgres.fields.JSONField(blank=True, null=True)
    cpus_scheduled = models.FloatField(blank=True, null=True)
    mem_scheduled = models.FloatField(blank=True, null=True)
    disk_out_scheduled = models.FloatField(blank=True, null=True)
    disk_total_scheduled = models.FloatField(blank=True, null=True)
    pre_started = models.DateTimeField(blank=True, null=True)
    pre_completed = models.DateTimeField(blank=True, null=True)
    pre_exit_code = models.IntegerField(blank=True, null=True)
    job_started = models.DateTimeField(blank=True, null=True)
    job_completed = models.DateTimeField(blank=True, null=True)
    job_exit_code = models.IntegerField(blank=True, null=True)
    job_metrics = django.contrib.postgres.fields.JSONField(blank=True, null=True)
    post_started = models.DateTimeField(blank=True, null=True)
    post_completed = models.DateTimeField(blank=True, null=True)
    post_exit_code = models.IntegerField(blank=True, null=True)
    stdout = models.TextField(blank=True, null=True)
    stderr = models.TextField(blank=True, null=True)
    results_manifest = django.contrib.postgres.fields.JSONField(blank=True, null=True)
    results = django.contrib.postgres.fields.JSONField(blank=True, null=True)
    ended = models.DateTimeField(blank=True, db_index=True, null=True)
    last_modified = models.DateTimeField(blank=True, db_index=True, null=True)

    objects = JobExecutionManager()

    def create_canceled_job_exe_end_model(self, when):
        """Creates and returns a canceled job execution end for this job execution

        :param when: When the job execution was canceled
        :type when: :class:`datetime.datetime`
        :returns: The job execution end model
        :rtype: :class:`job.models.JobExecutionEnd`
        """

        return self.create_job_exe_end_model(TaskResults(do_validate=False), 'CANCELED', None, when)

    def create_job_exe_end_model(self, task_results, status, error_id, when):
        """Creates and returns a job execution end model for this job execution

        :param task_results: The task results for the execution
        :type task_results: :class:`job.execution.tasks.json.results.task_results.TaskResults`
        :param status: The final job execution status
        :type status: str
        :param error_id: The ID of the error (for failed executions), possibly None
        :type error_id: int
        :param when: When the job execution ended
        :type when: :class:`datetime.datetime`
        :returns: The job execution end model
        :rtype: :class:`job.models.JobExecutionEnd`
        """

        job_exe_end = JobExecutionEnd()
        job_exe_end.job_exe_id = self.id
        job_exe_end.job_id = self.job_id
        job_exe_end.job_type_id = self.job_type_id
        job_exe_end.exe_num = self.exe_num
        job_exe_end.task_results = task_results.get_dict()
        job_exe_end.status = status
        job_exe_end.error_id = error_id
        job_exe_end.node_id = self.node_id
        job_exe_end.queued = self.queued
        job_exe_end.started = self.started
        job_exe_end.seed_started = task_results.get_task_started('main')
        job_exe_end.seed_ended = task_results.get_task_ended('main')
        job_exe_end.ended = when
        return job_exe_end

    def get_cluster_id(self):
        """Gets the cluster ID for the job execution

        :returns: The cluster ID for the job execution
        :rtype: string
        """

        if not self.cluster_id:
            # Return old-style format before cluster_id field was created
            return 'scale_%d' % self.pk

        return self.cluster_id

    def get_execution_configuration(self):
        """Returns the configuration for this job execution

        :returns: The configuration for this job execution
        :rtype: :class:`job.execution.configuration.json.exe_config.ExecutionConfiguration`
        """

        if isinstance(self.configuration, basestring):
            self.configuration = {}
        return ExecutionConfiguration(self.configuration, do_validate=False)

    def get_log_json(self, include_stdout=True, include_stderr=True, since=None):
        """Get log data from elasticsearch as a dict (from the raw JSON).

        :param include_stdout: If True, include stdout in the result
        :type include_stdout: bool
        :param include_stderr: If True include stderr in the result
        :type include_stderr: bool
        :param since: If present, only retrieve logs since this timestamp (non-inclusive).
        :type since: :class:`datetime.datetime` or None
        :rtype: tuple of (dict, :class:`datetime.datetime`) with the results or None and the last modified timestamp
        """

        if self.status == 'QUEUED':
            return None, timezone.now()

        if settings.ELASTICSEARCH_VERSION and settings.ELASTICSEARCH_VERISON.startswith('2.'):
            extension = ".raw"
        else:
            extension = ".keyword"

        q = {
                'size': 10000,
                'query': {
                    'bool': {
                        'must': [
                            {'term': {'scale_job_exe'+extension: self.get_cluster_id()}}
                        ]
                    }
                },
                'sort': [{'@timestamp': 'asc'}, {'scale_order_num': 'asc'}],
                '_source': ['@timestamp', 'scale_order_num', 'message', 'stream', 'scale_job_exe']
            }
        if not include_stdout and not include_stderr:
            return None, timezone.now()
        elif include_stdout and not include_stderr:
            q['query']['bool']['must'].append({'term': {'stream'+extension: 'stdout'}})
        elif include_stderr and not include_stdout:
            q['query']['bool']['must'].append({'term': {'stream'+extension: 'stderr'}})
        if since is not None:
            q['query']['bool']['must'].append({'range': {'@timestamp': {'gte': since.isoformat()}}})

        hits = settings.ELASTICSEARCH.search(index='logstash-*', body=q)

        if hits['hits']['total'] == 0:
            return None, timezone.now()
        last_modified = max([util.parse.parse_datetime(h['_source']['@timestamp']) for h in hits['hits']['hits']])
        return hits, last_modified

    def get_log_text(self, include_stdout=True, include_stderr=True, since=None, html=False):
        """Get log data from elasticsearch.

        :param include_stdout: If True, include stdout in the result
        :type include_stdout: bool
        :param include_stderr: If True include stderr in the result
        :type include_stderr: bool
        :param since: If present, only retrieve logs since this timestamp (non-inclusive).
        :type since: :class:`datetime.datetime` or None
        :param html: If True, wrap the lines in div elements with stdout/stderr css classes, otherwise use plain text
        :type html: bool
        :rtype: tuple of (str, :class:`datetime.datetime`) with the log or None and last modified timestamp
        """

        hits, last_modified = self.get_log_json(include_stdout, include_stderr, since)
        if hits is None:
            return None, last_modified
        valid_hits = []  # Make sure hits have the required message field
        for h in hits['hits']['hits']:
            if 'message' in h['_source']:
                valid_hits.append(h)
        if html:
            d = ''
            for h in valid_hits:
                cls = h['_source']['stream']
                d += '<div class="%s">%s</div>\n' % (cls, django.utils.html.escape(h['_source']['message']))
            return d, last_modified
        return '\n'.join(h['_source']['message'] for h in valid_hits), last_modified

    def get_resources(self):
        """Returns the resources allocated to this job execution

        :returns: The allocated resources
        :rtype: :class:`node.resources.node_resources.NodeResources`
        """

        if isinstance(self.resources, basestring):
            self.resources = {}

        logger.debug('Job execution for job id %d using resources: %s' % (self.job.id,
                                                                          self.resources))

        return Resources(self.resources, do_validate=False).get_node_resources()

    def get_v6_resources_json(self):
        """Returns the resources allocated to this job execution in v6 of the JSON schema

        :returns: The job resources in v6 of the JSON schema
        :rtype: dict
        """

        return rest_utils.strip_schema_version(self.get_resources().get_json().get_dict())

    def get_status(self):
        """Returns the status of this job execution

        :returns: The status of the job execution
        :rtype: string
        """

        try:
            return self.jobexecutionend.status
        except JobExecutionEnd.DoesNotExist:
            return 'RUNNING'

    @staticmethod
    def parse_cluster_id(task_id):
        """Parses and returns the cluster ID from the given task ID

        :param task_id: The task ID
        :type task_id: string
        :returns: The cluster ID
        :rtype: string
        """

        # Cluster ID is the first four segments
        segments = task_id.split('_')
        return '_'.join(segments[:4])

    def set_cluster_id(self, framework_id, job_id, exe_num):
        """Sets the unique cluster ID for this job execution

        :param framework_id: The scheduling framework ID
        :type framework_id: string
        :param job_id: The job ID
        :type job_id: int
        :param exe_num: The number of the execution
        :type exe_num: int
        """

        self.cluster_id = '%s_%s_%dx%d' % (JOB_TASK_ID_PREFIX, framework_id, job_id, exe_num)

    class Meta(object):
        """Meta information for the database"""
        db_table = 'job_exe'
        index_together = ['job', 'exe_num']


class JobExecutionEndManager(models.Manager):
    """Provides additional methods for handling job execution ends."""

    def get_recent_job_exe_end_metrics(self, when):
        """Returns the recent job_exe_end models that were COMPLETED or FAILED after the given time. The related
        job_exe, job_type, and error models will be populated.

        :param when: Returns executions that finished after this time
        :type when: :class:`datetime.datetime`
        :returns: The list of job_exe_end models with related job_exe, job_type, and error models
        :rtype: list
        """

        job_exe_end_query = self.select_related('job_exe', 'job_type', 'error')
        job_exe_end_query = job_exe_end_query.filter(status__in=['COMPLETED', 'FAILED'], ended__gte=when)
        job_exe_end_query = job_exe_end_query.defer('task_results')
        return job_exe_end_query


class JobExecutionEnd(models.Model):
    """Represents the end of a job execution, including the execution's final status and end time

    :keyword job_exe: The primary key to the scheduled job execution
    :type job_exe: :class:`django.db.models.ForeignKey`
    :keyword job: The job that was executed
    :type job: :class:`django.db.models.ForeignKey`
    :keyword job_type: The type of the job that was executed
    :type job_type: :class:`django.db.models.ForeignKey`
    :keyword exe_num: The number of the job's execution
    :type exe_num: :class:`django.db.models.IntegerField`

    :keyword task_results: JSON description of the task results
    :type task_results: :class:`django.contrib.postgres.fields.JSONField`
    :keyword status: The final status of the execution
    :type status: :class:`django.db.models.CharField`
    :keyword error: The error that caused the failure (should only be set when status is FAILED)
    :type error: :class:`django.db.models.ForeignKey`
    :keyword node: The node on which the job execution was run (None if it was canceled before being scheduled)
    :type node: :class:`django.db.models.ForeignKey`

    :keyword queued: When the job execution was added to the queue
    :type queued: :class:`django.db.models.DateTimeField`
    :keyword started: When the job execution was started (scheduled)
    :type started: :class:`django.db.models.DateTimeField`
    :keyword seed_started: When the Seed container was started (main task)
    :type seed_started: :class:`django.db.models.DateTimeField`
    :keyword seed_ended: When the Seed container ended (main task)
    :type seed_ended: :class:`django.db.models.DateTimeField`
    :keyword ended: When the job execution ended
    :type ended: :class:`django.db.models.DateTimeField`
    :keyword created: When this model was created
    :type created: :class:`django.db.models.DateTimeField`
    """

    JOB_EXE_END_STATUSES = (
        ('FAILED', 'FAILED'),
        ('COMPLETED', 'COMPLETED'),
        ('CANCELED', 'CANCELED'),
    )

    job_exe = models.OneToOneField('job.JobExecution', primary_key=True, on_delete=models.PROTECT)
    job = models.ForeignKey('job.Job', on_delete=models.PROTECT)
    job_type = models.ForeignKey('job.JobType', on_delete=models.PROTECT)
    exe_num = models.IntegerField()

    task_results = django.contrib.postgres.fields.JSONField(default=dict)
    status = models.CharField(choices=JOB_EXE_END_STATUSES, max_length=50, db_index=True)
    error = models.ForeignKey('error.Error', blank=True, null=True, on_delete=models.PROTECT)
    node = models.ForeignKey('node.Node', blank=True, null=True, on_delete=models.PROTECT)

    queued = models.DateTimeField()
    started = models.DateTimeField(blank=True, db_index=True, null=True)
    seed_started = models.DateTimeField(blank=True, null=True)
    seed_ended = models.DateTimeField(blank=True, null=True)
    ended = models.DateTimeField(db_index=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = JobExecutionEndManager()

    def get_task_results(self):
        """Returns the task results for this job execution

        :returns: The task results for this job execution
        :rtype: :class:`job.execution.tasks.json.results.task_results.TaskResults`
        """

        return TaskResults(self.task_results, do_validate=False)

    class Meta(object):
        """Meta information for the database"""
        db_table = 'job_exe_end'
        index_together = ['job', 'exe_num']


class JobExecutionOutput(models.Model):
    """Represents the output of a job execution

    :keyword job_exe: The primary key to the scheduled job execution
    :type job_exe: :class:`django.db.models.ForeignKey`
    :keyword job: The job that was executed
    :type job: :class:`django.db.models.ForeignKey`
    :keyword job_type: The type of the job that was executed
    :type job_type: :class:`django.db.models.ForeignKey`
    :keyword exe_num: The number of the job's execution
    :type exe_num: :class:`django.db.models.IntegerField`

    :keyword output: JSON description of the job execution's output
    :type output: :class:`django.contrib.postgres.fields.JSONField`

    :keyword created: When this model was created
    :type created: :class:`django.db.models.DateTimeField`
    """

    job_exe = models.OneToOneField('job.JobExecution', primary_key=True, on_delete=models.PROTECT)
    job = models.ForeignKey('job.Job', on_delete=models.PROTECT)
    job_type = models.ForeignKey('job.JobType', on_delete=models.PROTECT)
    exe_num = models.IntegerField()

    output = django.contrib.postgres.fields.JSONField(default=dict)

    created = models.DateTimeField(auto_now_add=True, db_index=True)

    def get_output(self):
        """Returns the output for this job execution

        :returns: The output for this job execution
        :rtype: :class:`job.configuration.results.job_results.JobResults`
        """

        # TODO: Remove old JobResults in v6 when we transition to only Seed job types
        if self.output and 'version' in self.output and '2.0' == self.output['version']:
            job_results = JobResults(self.output)
        else:
            job_results = JobResults_1_0(self.output)
        return job_results

    class Meta(object):
        """Meta information for the database"""
        db_table = 'job_exe_output'
        index_together = ['job', 'exe_num']


class JobInputFileManager(models.Manager):
    """Provides additional methods for handleing JobInputFiles"""

    def get_job_input_files(self, job_id, started=None, ended=None, time_field=None, file_name=None, job_input=None):
        """Returns a query for Input Files filtered on the given fields.

        :param job_id: The job ID
        :type job_id: int
        :param started: Query Scale files updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query Scale files updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :keyword time_field: The time field to use for filtering.
        :type time_field: string
        :param file_name: Query Scale files with the given file name.
        :type file_name: str
        :param job_input: The name of the job input that the file was passed into
        :type job_input: str
        :returns: The Scale file query
        :rtype: :class:`django.db.models.QuerySet`
        """

        files = ScaleFile.objects.filter_files_v5(started=started, ended=ended, time_field=time_field,
                                                  file_name=file_name)

        files = files.filter(jobinputfile__job=job_id).order_by('last_modified')

        if job_input:
            files = files.filter(jobinputfile__job_input=job_input)

        # Reach back to the job_data to get input_file data for legacy jobs
        if not files:
            job_data = Job.objects.get(pk=job_id).get_job_data()
            job_input_files = job_data.get_input_file_info()

            if job_input:
                job_input_file_ids = [f_id for f_id, name in job_input_files if name == job_input]
            else:
                job_input_file_ids = [f_id for f_id, name in job_input_files]

            files = ScaleFile.objects.filter_files_v5(started=started, ended=ended, time_field=time_field,
                                                      file_name=file_name)

            files = files.filter(id__in=job_input_file_ids).order_by('last_modified')

        return files


class JobInputFile(models.Model):
    """Links a job and its input files together. A file can be used as input to multiple jobs and a job can
    accept multiple input files.

    :keyword job: The job that the input file is linked to
    :type job: :class:`django.db.models.ForeignKey`
    :keyword input_file: The input file that is linked to the job
    :type input_file: :class:`django.db.models.ForeignKey`
    :keyword job_input: The name of the job input that the file was passed into
    :type job_input: :class:`django.db.models.CharField`
    :keyword created: When this link was created
    :type created: :class:`django.db.models.DateTimeField`
    """

    job = models.ForeignKey('job.Job', on_delete=models.PROTECT)
    input_file = models.ForeignKey('storage.ScaleFile', on_delete=models.PROTECT)
    job_input = models.CharField(max_length=250)
    created = models.DateTimeField(auto_now_add=True)

    objects = JobInputFileManager()

    class Meta(object):
        """meta information for the db"""
        db_table = 'job_input_file'


class JobTypeStatusCounts(object):
    """Represents job counts for a job type.

    :keyword status: The job execution status being counted.
    :type status: string
    :keyword count: The number of job executions for the associated status.
    :type count: int
    :keyword most_recent: The date/time of the last job execution for the associated status.
    :type most_recent: datetime.datetime
    :keyword category: The category of the job execution status being counted. Note that currently this will only be
        populated for types of ERROR status values.
    :type category: string
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
    :type job_counts: [:class:`job.models.JobTypeStatusCounts`]
    """
    def __init__(self, job_type, job_counts=None):
        self.job_type = job_type
        self.job_counts = job_counts


class JobTypePendingStatus(object):
    """Represents job type pending statistics.

    :keyword job_type: The job type being counted.
    :type job_type: :class:`job.models.JobType`
    :keyword count: The number of job executions pending for the associated job type.
    :type count: int
    :keyword longest_pending: The date/time of the last job execution for the associated job type.
    :type longest_pending: datetime.datetime
    """
    def __init__(self, job_type, count=0, longest_pending=None):
        self.job_type = job_type
        self.count = count
        self.longest_pending = longest_pending


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

    # TODO remove when REST API v5 is removed
    @transaction.atomic
    def create_job_type_v5(self, name, version, interface, trigger_rule=None, error_mapping=None,
                           custom_resources=None, configuration=None, secrets=None, **kwargs):
        """Creates a new non-system job type and saves it in the database. All database changes occur in an atomic
        transaction.

        :param name: The identifying name of the job type used by clients for queries
        :type name: string
        :param version: The version of the job type
        :type version: string
        :param interface: The interface for running a job of this type
        :type interface: :class:`job.configuration.interface.job_interface.JobInterface`
        :param trigger_rule: The trigger rule that creates jobs of this type, possibly None
        :type trigger_rule: :class:`trigger.models.TriggerRule`
        :param error_mapping: Mapping for translating an exit code to an error type
        :type error_mapping: :class:`job.error.mapping.JobErrorMapping`
        :param custom_resources: Custom resources required by this job type. Deprecated - remove with v5.
        :type custom_resources: :class:`node.resources.json.resources.Resources`
        :param configuration: The configuration for running a job of this type, possibly None
        :type configuration: :class:`job.configuration.json.job_config_2_0.JobConfigurationV2`
        :param secrets: Secret settings required by this job type
        :type secrets: dict
        :returns: The new job type
        :rtype: :class:`job.models.JobType`

        :raises :class:`job.exceptions.InvalidJobField`: If a given job type field has an invalid value
        :raises :class:`job.configuration.data.exceptions.InvalidConnection`: If the trigger rule connection to the job
        type interface is invalid
        """

        for field_name in kwargs:
            if field_name in JobType.UNEDITABLE_FIELDS:
                raise Exception('%s is not an editable field' % field_name)
        self._validate_job_type_fields(**kwargs)

        # Create the new job type
        job_type = JobType(**kwargs)
        job_type.name = name
        job_type.version = version
        job_type.version_array = job_type.get_job_version_array(version)
        job_type.manifest = interface.get_dict()
        if configuration:
            configuration.validate(job_type.manifest)
            job_type.configuration = configuration.get_dict()
        if error_mapping:
            error_mapping.validate_legacy()
            job_type.error_mapping = error_mapping.error_dict
        if custom_resources:
            job_type.custom_resources = custom_resources.get_dict()
        if 'is_active' in kwargs:
            job_type.deprecated = None if kwargs['is_active'] else timezone.now()
        if 'is_paused' in kwargs:
            job_type.paused = timezone.now() if kwargs['is_paused'] else None
        job_type.save()

        # Save any secrets to Vault
        if secrets:
            self.set_job_type_secrets(job_type.get_secrets_key(), secrets)

        # Create first revision of the job type
        JobTypeRevision.objects.create_job_type_revision(job_type)

        return job_type

    @transaction.atomic
    def create_job_type_v6(self, docker_image, manifest, icon_code=None, max_scheduled=None,
                           configuration=None, is_published=None):
        """Creates a new Seed job type and saves it in the database. All database changes occur in an atomic
        transaction.

        :param docker_image: The docker image containing the code to run for this job.
        :type docker_image: string
        :param manifest: The Seed Manifest defining the interface for running a job of this type
        :type manifest: :class:`job.seed.manifest.SeedManifest`
        :param icon_code: A font-awesome icon code to use when representing this job type.
        :type icon_code: string
        :param max_scheduled: Maximum  number of jobs of this type that may be scheduled to run at the same time.
        :type max_scheduled: integer
        :param configuration: The configuration for running a job of this type, possibly None
        :type configuration: :class:`job.configuration.configuration.JobConfiguration`
        :param is_published: Whether this job type has outputs that are published.
        :type is_published: bool
        :returns: The new job type
        :rtype: :class:`job.models.JobType`

        :raises :class:`job.exceptions.InvalidJobField`: If a given job type field has an invalid value
        """

        # Create/update any errors defined in manifest
        error_mapping = manifest.get_error_mapping()
        error_mapping.save_models()

        # Create the new job type
        job_type = JobType()

        job_type.populate_from_manifest(manifest)
        job_type.name = manifest.get_name()
        job_type.version = manifest.get_job_version()
        job_type.version_array = job_type.get_job_version_array(job_type.version)

        job_type.docker_image = docker_image

        if not configuration:
            configuration = JobConfiguration()
        configuration.validate(manifest)
        secrets = configuration.remove_secret_settings(manifest)
        job_type.configuration = convert_config_to_v6_json(configuration).get_dict()

        if icon_code:
            job_type.icon_code = icon_code
        if is_published:
            job_type.is_published = is_published
        if max_scheduled:
            job_type.max_scheduled = max_scheduled
        job_type.save()

        # Save any secrets to Vault
        if secrets:
            self.set_job_type_secrets(job_type.get_secrets_key(), secrets)

        # Create first revision of the job type
        JobTypeRevision.objects.create_job_type_revision(job_type)

        JobTypeTag.objects.update_job_type_tags(job_type, manifest)

        return job_type

    # TODO: remove this when REST API v5 is removed
    def convert_manifest_to_v5_interface(self, manifest):
        """Parses a Seed manifest interface definition and reshapes it to match the format of the old style
        interface.  This is done so that v5 API calls to get job details can still receive information about
        new Seed style job types.

        :param manifest: The Seed Manifest interface definition
        :type manifest: dict
        :returns: The converted manifest
        :rtype: dict
        """

        manifest = manifest['job']['interface'] if ('job' in manifest) and ('interface' in manifest['job']) else {}

        interface = {}
        interface['settings'] = manifest['settings'] if 'settings' in manifest else []
        interface['mounts'] = manifest['mounts'] if 'mounts' in manifest else []
        interface['output_data'] = manifest['outputs']['files'] if ('outputs' in manifest) and ('files' in manifest['outputs']) else []
        interface['input_data'] = manifest['inputs']['files'] if ('inputs' in manifest) and ('files' in manifest['inputs']) else []
        interface['env_vars'] = manifest['inputs']['json'] if ('inputs' in manifest) and ('json' in manifest['inputs']) else []
        interface['shared_resources'] = []
        interface['version'] = '1.4'
        interface['command'] = ''
        interface['command_arguments'] = manifest['command'] if 'command' in manifest else ''

        return interface

    @transaction.atomic
    def edit_job_type_v5(self, job_type_id, interface=None, trigger_rule=None, remove_trigger_rule=False,
                         error_mapping=None, custom_resources=None, configuration=None, secrets=None, **kwargs):
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
        :type error_mapping: :class:`job.error.mapping.JobErrorMapping`
        :param custom_resources: Custom resources required by this job type
        :type custom_resources: :class:`node.resources.json.resources.Resources`
        :param configuration: The configuration for running a job of this type, possibly None
        :type configuration: :class:`job.configuration.json.job_config_2_0.JobConfigurationV2`
        :param secrets: Secret settings required by this job type
        :type secrets: dict

        :raises :class:`job.exceptions.InvalidJobField`: If a given job type field has an invalid value
        :raises :class:`job.configuration.data.exceptions.InvalidConnection`: If the trigger rule connection to the job
        type interface is invalid
        :raises :class:`recipe.configuration.definition.exceptions.InvalidDefinition`: If the interface change
        invalidates any existing recipe type definitions
        """

        for field_name in kwargs:
            if field_name in JobType.UNEDITABLE_FIELDS:
                raise Exception('%s is not an editable field' % field_name)
        self._validate_job_type_fields(**kwargs)

        # Acquire model lock for job type
        job_type = JobType.objects.select_for_update().get(pk=job_type_id)
        if job_type.is_system:
            if len(kwargs) > 1 or 'is_paused' not in kwargs:
                raise InvalidJobField('You can only modify the is_paused field for a System Job')

        # Check for backdoor editing of seed job types
        if job_type.is_seed_job_type():
            v6_fields = {'icon_code', 'is_active', 'is_paused', 'is_published', 'max_scheduled', 'configuration'}
            for field_name in kwargs:
                if field_name not in v6_fields:
                    raise InvalidJobField('Invalid field: %s \n Only the following fields are editable for seed job types: %s ' % (field_name, v6_fields))
            if interface or error_mapping or custom_resources or secrets:
                raise InvalidJobField('Only the following fields are editable for seed job types: %s ' % v6_fields)

        recipe_types = []
        if interface:
            # Lock all recipe types so they can be validated after changing job type interface
            from recipe.models import RecipeType
            recipe_types = list(RecipeType.objects.select_for_update().order_by('id').iterator())

        if interface:
            # New job interface, validate all existing recipes
            job_type.manifest = interface.get_dict()
            job_type.revision_num += 1
            job_type.save()
            for recipe_type in recipe_types:
                recipe_type.get_recipe_definition().validate_job_interfaces()

        # New job configuration
        if configuration:
            configuration.validate(job_type.manifest)
            job_type.configuration = configuration.get_dict()

        if error_mapping:
            error_mapping.validate_legacy()
            job_type.error_mapping = error_mapping.error_dict

        if custom_resources:
            job_type.custom_resources = custom_resources.get_dict()

        if 'is_active' in kwargs and job_type.is_active != kwargs['is_active']:
            job_type.deprecated = None if kwargs['is_active'] else timezone.now()
        if 'is_paused' in kwargs and job_type.is_paused != kwargs['is_paused']:
            job_type.paused = timezone.now() if kwargs['is_paused'] else None
        for field_name in kwargs:
            setattr(job_type, field_name, kwargs[field_name])
        job_type.unmet_resources = None #assume edit is fixing resources; reset unmet_resources
        job_type.save()

        # Save any secrets to Vault
        if secrets:
            self.set_job_type_secrets(job_type.get_secrets_key(), secrets)

        if interface:
            # Create new revision of the job type for new interface
            JobTypeRevision.objects.create_job_type_revision(job_type)

    @transaction.atomic
    def edit_job_type_v6(self, job_type_id, manifest=None, docker_image=None, icon_code=None, is_active=None,
                         is_paused=None, is_published=None, max_scheduled=None, configuration=None, auto_update=None):
        """Edits the given job type and saves the changes in the database.
        All database changes occur in an atomic transaction. An argument of None for a field
        indicates that the field should not change.

        :param job_type_id: The unique identifier of the job type to edit
        :type job_type_id: int
        :param manifest: The Seed Manifest defining the interface for running a job of this type
        :type manifest: :class:`job.seed.manifest.SeedManifest`
        :param docker_image: The docker image containing the code to run for this job.
        :type docker_image: string
        :param icon_code: A font-awesome icon code to use when representing this job type.
        :type icon_code: string
        :param is_active: Whether this job type is active or deprecated.
        :type is_active: bool
        :param is_paused: Whether this job type is paused and should not have jobs scheduled or not
        :type is_paused: bool
        :param is_published: Whether this job type has outputs that are published.
        :type is_published: bool
        :param max_scheduled: Maximum  number of jobs of this type that may be scheduled to run at the same time.
        :type max_scheduled: integer
        :param configuration: The configuration for running a job of this type, possibly None
        :type configuration: :class:`job.configuration.configuration.JobConfiguration`
        :param auto_update: If true, recipes that contain this job type will automatically be updated
        :type auto_update: bool

        :raises :class:`job.exceptions.InvalidJobField`: If a given job type field has an invalid value
        """
        from recipe.messages.update_recipe_definition import create_job_update_recipe_definition_message
        from recipe.models import RecipeTypeJobLink

        # Acquire model lock for job type
        job_type = JobType.objects.select_for_update().get(pk=job_type_id)
        if job_type.is_system:
            if manifest or icon_code or is_active or max_scheduled or configuration:
                raise InvalidJobField('You can only modify the is_paused field for a System Job')

        if manifest:
            currentManifest = manifest
            job_type.revision_num += 1

            # Create/update any errors defined in manifest
            error_mapping = manifest.get_error_mapping()
            error_mapping.save_models()

            job_type.populate_from_manifest(manifest)
            job_type.unmet_resources = None #assume edit is fixing resources; reset unmet_resources
            job_type.save()
            JobTypeTag.objects.update_job_type_tags(job_type, manifest)
        else:
            currentManifest = SeedManifest(job_type.manifest)

        if not configuration:
            configuration = job_type.get_job_configuration()
        configuration.validate(currentManifest)
        secrets = configuration.remove_secret_settings(currentManifest)
        job_type.configuration = convert_config_to_v6_json(configuration).get_dict()

        if docker_image:
            job_type.docker_image = docker_image
        if icon_code:
            job_type.icon_code = icon_code
        if is_active and job_type.is_active != is_active:
            job_type.deprecated = None if is_active else timezone.now()
            job_type.is_active = is_active
        if is_paused and job_type.is_paused != is_paused:
            job_type.paused = timezone.now() if is_paused else None
            job_type.is_paused = is_paused
        if is_published:
            job_type.is_published = is_published
        if max_scheduled:
            job_type.max_scheduled = max_scheduled

        job_type.save()

        # Save any secrets to Vault
        if secrets:
            self.set_job_type_secrets(job_type.get_secrets_key(), secrets)

        if manifest:
            # Create new revision of the job type for new interface
            JobTypeRevision.objects.create_job_type_revision(job_type)
            # Update recipes containing this job type
            if auto_update:
                recipe_ids = RecipeTypeJobLink.objects.get_recipe_type_ids([job_type.id])
                msgs = [create_job_update_recipe_definition_message(id, job_type.id) for id in recipe_ids]
                CommandMessageManager().send_messages(msgs)

    def get_by_natural_key(self, name, version):
        """Django method to retrieve a job type for the given natural key

        :param name: The human-readable name of the job type
        :type name: string
        :param version: The version of the job type
        :type version: string
        :returns: The job type defined by the natural key
        :rtype: :class:`job.models.JobType`
        """
        return self.get(name=name, version=version)

    def get_clock_job_type(self):
        """Returns the Scale Clock job type

        :returns: The clock job type
        :rtype: :class:`job.models.JobType`
        """

        return JobType.objects.get(name='scale-clock', version='1.0')

    def get_job_types(self, started=None, ended=None, names=None, categories=None, is_active=True, is_operational=None,
                      order=None):
        """Returns a list of job types within the given time range.

        :param started: Query job types updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query job types updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param names: Query jobs of the type associated with the name.
        :type names: [string]
        :param categories: Query jobs of the type associated with the category.
        :type categories: [string]
        :param is_active: Query job types that are actively available for use.
        :type is_active: bool
        :param is_operational: Query job types that are operational or research phase.
        :type is_operational: bool
        :param order: A list of fields to control the sort order.
        :type order: [string]
        :returns: The list of job types that match the time range.
        :rtype: [:class:`job.models.JobType`]
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
        if is_active is not None:
            job_types = job_types.filter(is_active=is_active)
        if is_operational is not None:
            job_types = job_types.filter(is_operational=is_operational)

        # Apply sorting
        if order:
            job_types = job_types.order_by(*order)
        else:
            job_types = job_types.order_by('last_modified')
        return job_types

    def get_job_types_v6(self, keywords=None, ids=None, is_active=None, is_system=None, order=None):
        """Returns a list of all job types

        :param keywords: Query job types with name, title, description or tag matching one of the specified keywords
        :type keywords: list
        :param ids: Query job types with a version matching the given ids
        :type keyword: list
        :param is_active: Query job types that are actively available for use.
        :type is_active: bool
        :param is_system: Query job types that are system job types.
        :type is_operational: bool
        :param order: A list of fields to control the sort order.
        :type order: list
        :returns: The list of latest version of job types that match the given parameters.
        :rtype: list
        """

        # Execute a sub-query that returns distinct job type names that match the provided filter arguments
        job_types = self.all()
        if keywords:
            key_query = Q()
            for keyword in keywords:
                key_query |= Q(name__icontains=keyword)
                key_query |= Q(title__icontains=keyword)
                key_query |= Q(description__icontains=keyword)
                key_query |= Q(jobtypetag__tag__icontains=keyword)
            job_types = job_types.filter(key_query)
        if ids:
            job_types = job_types.filter(id__in=ids)
        if is_active is not None:
            job_types = job_types.filter(is_active=is_active)
        if is_system is not None:
            job_types = job_types.filter(is_system=is_system)

        # Apply sorting
        if order:
            job_types = job_types.order_by(*order)
        else:
            job_types = job_types.order_by('last_modified')

        return job_types


    def get_job_type_names_v6(self, keywords=None, ids=None, is_active=None, is_system=None, order=None):
        """Returns a list of the latest version of job types

        :param keywords: Query job types with name, title, description or tag matching one of the specified keywords
        :type keywords: list
        :param ids: Query job types with a version matching the given ids
        :type keyword: list
        :param is_active: Query job types that are actively available for use.
        :type is_active: bool
        :param is_system: Query job types that are system job types.
        :type is_operational: bool
        :param order: A list of fields to control the sort order.
        :type order: list
        :returns: The list of latest version of job types that match the given parameters.
        :rtype: list
        """

        # Execute a sub-query that returns distinct job type names that match the provided filter arguments
        sub_query = self.all()
        if keywords:
            key_query = Q()
            for keyword in keywords:
                key_query |= Q(name__icontains=keyword)
                key_query |= Q(title__icontains=keyword)
                key_query |= Q(description__icontains=keyword)
                key_query |= Q(jobtypetag__tag__icontains=keyword)
            sub_query = sub_query.filter(key_query)
        if ids:
            sub_query = sub_query.filter(id__in=ids)
        if is_active is not None:
            sub_query = sub_query.filter(is_active=is_active)
        if is_system is not None:
            sub_query = sub_query.filter(is_system=is_system)
        job_type_names = [result['name'] for result in sub_query.values('name').distinct('name')]

        if not job_type_names:
            return []

        versions_by_id = {}
        # Execute main query to find job type IDs and their matching num_versions
        qry = 'SELECT DISTINCT ON (jt.name) jt.id, nv.versions FROM job_type jt '
        qry += 'JOIN (SELECT name, array_agg(version) AS versions FROM job_type GROUP BY name) nv ON jt.name = nv.name '
        qry += 'WHERE jt.name IN %s '
        qry += 'ORDER BY jt.name, jt.version_array DESC'
        with connection.cursor() as cursor:
            cursor.execute(qry, [tuple(job_type_names)])
            for row in cursor.fetchall():
                versions_by_id[row[0]] = row[1]

        # Retrieve job types by ID
        job_types = self.filter(id__in=versions_by_id.keys())
        # Apply sorting
        if order:
            job_types = job_types.order_by(*order)
        else:
            job_types = job_types.order_by('last_modified')

        # Add num_versions to each job type
        results = []
        for job_type in job_types:
            job_type.versions = versions_by_id[job_type.id]
            results.append(job_type)
        return results

    def get_recipe_job_type_ids(self, definition):
        """Gets the model ids of the job types contained in the given RecipeDefinition

        :param definition: RecipeDefinition to search for job types
        :type definition: :class:`recipe.definition.definition.RecipeDefinition`
        :returns: set of JobType ids
        :rtype: set[int]
        """

        types = definition.get_job_type_keys()
        ids = []
        if types:
            query = reduce(
                operator.or_,
                (Q(name=type.name, version=type.version) for type in types)
                )
            ids = self.all().filter(query).values_list('pk', flat=True)

        return ids

    def get_job_type_versions_v6(self, name, is_active=None, order=None):
        """Returns a list of the versions of the job type with the given name

        :param name: Name of the job type
        :type name: string
        :param is_active: Query job types that are actively available for use.
        :type is_active: bool
        :param order: A list of fields to control the sort order.
        :type order: [string]
        :returns: The list of versions of the job type that match the given parameters.
        :rtype: [:class:`job.models.JobType`]
        """

        # Fetch a list of job types
        job_types = JobType.objects.all()

        job_types = job_types.filter(name=name)

        if is_active is not None:
            job_types = job_types.filter(is_active=is_active)

        # Apply sorting
        if order:
            job_types = job_types.order_by(*order)
        else:
            job_types = job_types.order_by('last_modified')

        return job_types

    def get_details_v5(self, job_type_id):
        """Returns the job type for the given ID with all detail fields included.

        The additional fields include: errors, job_counts_6h, job_counts_12h, and job_counts_24h.

        :param job_type_id: The unique identifier of the job type.
        :type job_type_id: int
        :returns: The job type with all detail fields included.
        :rtype: :class:`job.models.JobType`
        """

        # Attempt to get the job type
        job_type = JobType.objects.get(pk=job_type_id)

        # Add associated error information
        error_names = job_type.get_error_mapping().get_error_names_legacy()
        job_type.errors = Error.objects.filter(name__in=error_names) if error_names else []

        # Scrub configuration for secrets
        if job_type.configuration:
            if JobInterfaceSunset.is_seed_dict(job_type.manifest):
                configuration = job_type.get_job_configuration()
                manifest = SeedManifest(job_type.manifest, do_validate=False)
                configuration.remove_secret_settings(manifest)
                job_type.configuration = convert_config_to_v6_json(configuration).get_dict()
            else:
                configuration = JobConfigurationV2(job_type.configuration)
                interface = JobInterfaceSunset.create(job_type.manifest)
                configuration.validate(interface.get_dict())
                job_type.configuration = configuration.get_dict()

        # Add recent performance statistics
        started = timezone.now()
        job_type.job_counts_24h = self.get_performance(job_type_id, started - datetime.timedelta(hours=24))
        job_type.job_counts_12h = self.get_performance(job_type_id, started - datetime.timedelta(hours=12))
        job_type.job_counts_6h = self.get_performance(job_type_id, started - datetime.timedelta(hours=6))

        return job_type

    def get_details_v6(self, name, version):
        """Returns the job type for the given name and version with all detail fields included.

        The additional fields include: errors, job_counts_6h, job_counts_12h, and job_counts_24h.

        :param name: The name of the job type.
        :type name: string
        :param version: The version of the job type.
        :type version: string
        :returns: The job type with all detail fields included.
        :rtype: :class:`job.models.JobType`
        """

        # Attempt to get the job type
        job_type = JobType.objects.all().get(name=name, version=version)

        # V6 does not support non seed job types
        if not job_type.is_seed_job_type():
            raise NonSeedJobType('Job type %s version %s is not a Seed image. Please update your image or use the legacy v5 interface' % (name, version))


        # Scrub configuration for secrets
        if job_type.configuration:
            configuration = job_type.get_job_configuration()
            manifest = SeedManifest(job_type.manifest, do_validate=False)
            configuration.remove_secret_settings(manifest)

        return job_type

    def get_performance(self, job_type_id, started, ended=None):
        """Returns the job count statistics for a given job type and time range.

        :param job_type_id: The unique identifier of the job type.
        :type job_type_id: int
        :param started: Query job types updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query job types updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :returns: A list of job counts organized by status.
        :rtype: [:class:`job.models.JobTypeStatusCounts`]
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

    def get_status(self, started, ended=None, is_operational=None):
        """Returns a list of job types with counts broken down by job status.

        Note that all running job types are counted regardless of date/time filters.

        :param started: Query job types updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query job types updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param is_operational: Query job types that are operational or research phase.
        :type is_operational: bool
        :returns: The list of job types with supplemented statistics.
        :rtype: [:class:`job.models.JobTypeStatus`]
        """

        # Build a mapping of all job type identifier -> status model
        job_types = JobType.objects.all().defer('manifest', 'error_mapping').order_by('last_modified')
        if is_operational is not None:
            job_types = job_types.filter(is_operational=is_operational)
        status_dict = {job_type.id: JobTypeStatus(job_type, []) for job_type in job_types}

        # Build up the filters based on inputs and all running jobs
        count_filters = Q(status='RUNNING')
        if ended:
            count_filters = count_filters | Q(last_status_change__gte=started, last_status_change__lte=ended)
        else:
            count_filters = count_filters | Q(last_status_change__gte=started)

        # Fetch a count of all jobs grouped by status counts
        count_dicts = Job.objects.values('job_type__id', 'status', 'error__category').filter(count_filters)
        if is_operational is not None:
            count_dicts = count_dicts.filter(job_type__is_operational=is_operational)
        count_dicts = count_dicts.annotate(count=models.Count('job_type'),
                                           most_recent=models.Max('last_status_change'))

        # Collect the status and counts by job type
        for count_dict in count_dicts:
            status = status_dict[count_dict['job_type__id']]
            counts = JobTypeStatusCounts(count_dict['status'], count_dict['count'],
                                         count_dict['most_recent'], count_dict['error__category'])
            status.job_counts.append(counts)

        return [status_dict[job_type.id] for job_type in job_types]

    def get_pending_status(self):
        """Returns a status overview of all currently pending job types.

        The results consist of standard job type models, plus additional computed statistics fields including a total
        count of associated jobs and the longest pending job.

        :returns: The list of each job type with additional statistic fields.
        :rtype: [:class:`job.models.JobTypePendingStatus`]
        """

        # Fetch a count of all pending jobs with type information
        # We have to specify values to workaround the JSON fields throwing an error when used with annotate
        job_dicts = Job.objects.values(*['job_type__%s' % f for f in JobType.BASE_FIELDS])
        job_dicts = job_dicts.filter(status='PENDING')
        job_dicts = job_dicts.annotate(count=models.Count('job_type'),
                                       longest_pending=models.Min('last_status_change'))
        job_dicts = job_dicts.order_by('longest_pending')

        # Convert each result to a real job type model with added statistics
        results = []
        for job_dict in job_dicts:
            job_type_dict = {f: job_dict['job_type__%s' % f] for f in JobType.BASE_FIELDS}
            job_type = JobType(**job_type_dict)

            status = JobTypePendingStatus(job_type, job_dict['count'], job_dict['longest_pending'])
            results.append(status)
        return results

    def get_running_status(self):
        """Returns a status overview of all currently running job types.

        The results consist of standard job type models, plus additional computed statistics fields including a total
        count of associated jobs and the longest running job.

        :returns: The list of each job type with additional statistic fields.
        :rtype: [:class:`job.models.JobTypeRunningStatus`]
        """

        # Fetch a count of all running jobs with type information
        # We have to specify values to workaround the JSON fields throwing an error when used with annotate
        job_dicts = Job.objects.values(*['job_type__%s' % f for f in JobType.BASE_FIELDS])
        job_dicts = job_dicts.filter(status='RUNNING')
        job_dicts = job_dicts.annotate(count=models.Count('job_type'),
                                       longest_running=models.Min('last_status_change'))
        job_dicts = job_dicts.order_by('longest_running')

        # Convert each result to a real job type model with added statistics
        results = []
        for job_dict in job_dicts:
            job_type_dict = {f: job_dict['job_type__%s' % f] for f in JobType.BASE_FIELDS}
            job_type = JobType(**job_type_dict)

            status = JobTypeRunningStatus(job_type, job_dict['count'], job_dict['longest_running'])
            results.append(status)
        return results

    def get_failed_status(self):
        """Returns all job types that have failed due to system errors.

        The results consist of standard job type models, plus additional computed statistics fields including a total
        count of associated jobs and the last status change of a running job.

        :returns: The list of each job type with additional statistic fields.
        :rtype: [:class:`job.models.JobTypeFailedStatus`]
        """

        # Make a list of all the basic error fields to fetch
        error_fields = ['id', 'name', 'title', 'description', 'category', 'created', 'last_modified']

        # We have to specify values to workaround the JSON fields throwing an error when used with annotate
        query_fields = []
        query_fields.extend(['job_type__%s' % f for f in JobType.BASE_FIELDS])
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
            job_type_dict = {f: job_dict['job_type__%s' % f] for f in JobType.BASE_FIELDS}
            job_type = JobType(**job_type_dict)

            error_dict = {f: job_dict['error__%s' % f] for f in error_fields}
            error = Error(**error_dict)

            status = JobTypeFailedStatus(job_type, error, job_dict['count'], job_dict['first_error'],
                                         job_dict['last_error'])
            results.append(status)
        return results

    def set_job_type_secrets(self, secrets_key, secrets):
        """Sends request to SecretsHandler to write secrets for a job type.

        :param secrets_key: Reference pointer for job_type settings stored in secrets backend
        :type secrets_key: str
        :param secrets: Secret settings required by this job type.
        :type secrets: dict
        """

        secrets_handler = SecretsHandler()
        secrets_handler.set_job_type_secrets(secrets_key, secrets)

    def validate_job_type_v5(self, name, version, interface, error_mapping=None, trigger_config=None,
                             configuration=None):
        """Validates a new job type prior to attempting a save

        :param name: The system name of the job type
        :type name: string
        :param version: The version of the job type
        :type version: string
        :param interface: The interface for running a job of this type
        :type interface: :class:`job.configuration.interface.job_interface.JobInterface`
        :param error_mapping: Mapping for translating an exit code to an error type
        :type error_mapping: :class:`job.error.mapping.JobErrorMapping`
        :param trigger_config: The trigger rule configuration, possibly None
        :type trigger_config: :class:`trigger.configuration.trigger_rule.TriggerRuleConfiguration`
        :param configuration: The configuration for running a job of this type, possibly None
        :type configuration: :class:`job.configuration.json.job_config_2_0.JobConfigurationV2`
        :returns: A list of warnings discovered during validation.
        :rtype: [:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`recipe.configuration.definition.exceptions.InvalidDefinition`: If the interface invalidates any
            existing recipe type definitions
        """

        warnings = []

        if configuration:
            warnings.extend(configuration.validate(interface.get_dict()))

        if error_mapping:
            error_mapping.validate_legacy()

        try:
            # If this is an existing job type, try changing the interface temporarily and validate all existing recipe
            # type definitions
            with transaction.atomic():
                job_type = JobType.objects.get(name=name, version=version)
                job_type.manifest = interface.get_dict()
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

    def validate_job_type_v6(self, manifest_dict, configuration_dict=None):
        """Validates a new job type prior to attempting a save

        :param manifest_dict: The Seed Manifest defining the interface for running a job of this type
        :type manifest_dict: dict
        :param configuration_dict: The configuration for running a job of this type, possibly None
        :type configuration_dict: dict
        :returns: The job type validation.
        :rtype: :class:`job.models.JobTypeValidation`
        """

        is_valid = True
        errors = []
        warnings = []

        manifest = None
        config = None

        try:
            manifest = SeedManifest(manifest_dict, do_validate=True)
            config = JobConfigurationV6(configuration_dict, do_validate=True).get_configuration()
        except InvalidSeedManifestDefinition as ex:
            is_valid = False
            errors.append(ex.error)
            message = 'Job type manifest invalid: %s' % ex
            logger.info(message)
            pass
        except InvalidJobConfiguration as ex:
            is_valid = False
            errors.append(ex.error)
            message = 'Job type configuration invalid: %s' % ex
            logger.info(message)
            pass

        if config and manifest:
            try:
                warnings.extend(config.validate(manifest))
                resources = manifest.get_scalar_resources()
                for r in resources:
                    name = r['name'].lower()
                    if name not in ['cpus', 'mem', 'disk', 'gpus', 'sharedmem']:
                        msg = '\'%s\' is not a standard resouce. This job type might not be schedulable.'
                        warnings.append(ValidationWarning('NONSTANDARD_RESOURCE', msg % r['name']))
            except InvalidJobConfiguration as ex:
                is_valid = False
                errors.append(ex.error)
                message = 'Job type configuration invalid: %s' % ex
                logger.info(message)
                pass

        return JobTypeValidation(is_valid, errors, warnings)

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

    :keyword name: The identifying name of the job type used by clients for queries
    :type name: :class:`django.db.models.CharField`
    :keyword version: The version of the job type
    :type version: :class:`django.db.models.CharField`
    :keyword version_array: The version of the job type split into SemVer integer components (major,minor,patch,prerelease)
    :type version_array: list
    :keyword title: The human-readable name of the job type. Deprecated - remove with v5.
    :type title: :class:`django.db.models.CharField`
    :keyword description: An optional description of the job type. Deprecated - remove with v5.
    :type description: :class:`django.db.models.TextField`

    :keyword is_system: Whether this is a system type
    :type is_system: :class:`django.db.models.BooleanField`
    :keyword is_long_running: Whether this type is long running. A job of this type is intended to run for a long time,
        potentially indefinitely, without timing out and always being re-queued after a failure
    :type is_long_running: :class:`django.db.models.BooleanField`
    :keyword is_active: Whether the job type is active (false once job type is deprecated)
    :type is_active: :class:`django.db.models.BooleanField`
    :keyword is_paused: Whether the job type is paused (while paused no jobs of this type will be scheduled off of the
        queue)
    :type is_paused: :class:`django.db.models.BooleanField`
    :param is_published: Whether this job type has outputs that are published.
        :type is_published: :class:`django.db.models.BooleanField`

    :keyword unmet_resources: List of resource names that currently don't exist or aren't sufficient in the cluster
    :type unmet_resources: :class:`django.db.models.CharField`

    :keyword max_scheduled: The maximum number of jobs of this type that may be scheduled to run at the same time
    :type max_scheduled: :class:`django.db.models.IntegerField`
    :keyword max_tries: The maximum number of times to try executing a job in case of errors (minimum one)
    :type max_tries: :class:`django.db.models.IntegerField`
    :keyword icon_code: A font-awesome icon code (like 'f013' for gear) to use when representing this job type
    :type icon_code: string of a FontAwesome icon code

    :keyword revision_num: The current revision number of the interface, starts at one. Deprecated - remove with v5.
    :type revision_num: :class:`django.db.models.IntegerField`
    :keyword docker_image: The Docker image containing the code to run for this job (if uses_docker is True)
    :type docker_image: :class:`django.db.models.CharField`
    :keyword manifest: JSON description defining the manifest for running a job of this type (previously interface).
    :type manifest: :class:`django.contrib.postgres.fields.JSONField`
    :keyword configuration: JSON describing the default job configuration for jobs of this type
    :type configuration: :class:`django.contrib.postgres.fields.JSONField`

    :keyword created: When the job type was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword deprecated: When the job type was deprecated (no longer active)
    :type deprecated: :class:`django.db.models.DateTimeField`
    :keyword paused: When the job type was paused
    :type paused: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the job type was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`

    :keyword category: An optional overall category of the job type. Deprecated - remove with v5.
    :type category: :class:`django.db.models.CharField`
    :keyword author_name: The name of the person or organization that created the associated algorithm. Deprecated -
        remove with v5.
    :type author_name: :class:`django.db.models.CharField`
    :keyword author_url: The address to a home page about the author or associated algorithm. Deprecated - removed in
        v6.
    :type author_url: :class:`django.db.models.TextField`
    :keyword is_operational: Whether this job type is operational (True) or is still in a research & development (R&D)
        phase (False)
    :type is_operational: :class:`django.db.models.BooleanField`
    :keyword uses_docker: Whether the job type uses Docker. Deprecated - remove with v5.
    :type uses_docker: :class:`django.db.models.BooleanField`
    :keyword docker_privileged: Whether the job type uses Docker in privileged mode. Deprecated - remove with v5.
    :type docker_privileged: :class:`django.db.models.BooleanField`
    :keyword docker_params: JSON array of 2-tuples (key-value) which will be passed as-is to docker. See the mesos
        prototype file for further information. Deprecated - remove with v5.
    :type docker_params: :class:`django.contrib.postgres.fields.JSONField`
    :keyword error_mapping: Mapping for translating an exit code to an error type. Deprecated - remove with v5.
    :type error_mapping: :class:`django.contrib.postgres.fields.JSONField`
    :keyword trigger_rule: The rule to trigger new jobs of this type
    :type trigger_rule: :class:`django.db.models.ForeignKey`
    :keyword priority: The priority of the job type (lower number is higher priority)
    :type priority: :class:`django.db.models.IntegerField`
    :keyword timeout: The maximum amount of time to allow a job of this type to run before being killed (in seconds)
    :type timeout: :class:`django.db.models.IntegerField`
    :keyword cpus_required: The number of CPUs required for a job of this type. Deprecated - remove with v5.
    :type cpus_required: :class:`django.db.models.FloatField`
    :keyword mem_const_required: A constant amount of RAM in MiB required for a job of this type. Deprecated - removed
        in v6.
    :type mem_const_required: :class:`django.db.models.FloatField`
    :keyword mem_mult_required: A multiplier (2x = 2.0) applied to the size of the input files to determine additional
        RAM in MiB required for a job of this type. Deprecated - remove with v5.
    :type mem_mult_required: :class:`django.db.models.FloatField`
    :keyword shared_mem_required: The amount of shared memory (/dev/shm) in MiB required for a job of this type.
        Deprecated - remove with v5.
    :type shared_mem_required: :class:`django.db.models.FloatField`
    :keyword disk_out_const_required: A constant amount of disk space in MiB required for job output (temp work and
        products) for a job of this type. Deprecated - remove with v5.
    :type disk_out_const_required: :class:`django.db.models.FloatField`
    :keyword disk_out_mult_required: A multiplier (2x = 2.0) applied to the size of the input files to determine
        additional disk space in MiB required for job output (temp work and products) for a job of this type.
        Deprecated - remove with v5.
    :type disk_out_mult_required: :class:`django.db.models.FloatField`
    :keyword custom_resources: JSON describing the custom resources required for jobs of this type. Deprecated -
        remove with v5.
    :type custom_resources: :class:`django.contrib.postgres.fields.JSONField`
    """

    BASE_FIELDS = ('id', 'name', 'version', 'title', 'description', 'category', 'author_name', 'author_url',
                   'is_system', 'is_long_running', 'is_active', 'is_operational', 'is_paused', 'is_published',
                   'icon_code')

    UNEDITABLE_FIELDS = ('name', 'version', 'is_system', 'is_long_running', 'is_active', 'uses_docker', 'revision_num',
                         'created', 'deprecated', 'paused', 'last_modified')

    BASE_FIELDS_V6 = ('id', 'name', 'version', 'manifest', 'error_mapping', 'custom_resources',
                      'configuration')

    UNEDITABLE_FIELDS_V6 = ('is_system', 'revision_num', 'created', 'deprecated', 'last_modified')

    name = models.CharField(db_index=True, max_length=50)
    version = models.CharField(db_index=True, max_length=50)
    version_array = django.contrib.postgres.fields.ArrayField(models.IntegerField(null=True),default=list([None]*4),size=4)
    title = models.CharField(blank=True, max_length=50, null=True)
    description = models.TextField(blank=True, null=True)

    is_system = models.BooleanField(default=False)
    is_long_running = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_paused = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    unmet_resources = models.CharField(blank=True, max_length=250, null=True)

    max_scheduled = models.IntegerField(blank=True, null=True)
    max_tries = models.IntegerField(default=3)
    icon_code = models.CharField(max_length=20, null=True, blank=True)

    revision_num = models.IntegerField(default=1)
    docker_image = models.CharField(default='', max_length=500)
    manifest = django.contrib.postgres.fields.JSONField(default=dict)
    configuration = django.contrib.postgres.fields.JSONField(default=dict)

    created = models.DateTimeField(auto_now_add=True)
    deprecated = models.DateTimeField(blank=True, null=True)
    paused = models.DateTimeField(blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)

    # TODO: remove with v5 API and/or legacy job types
    category = models.CharField(db_index=True, blank=True, max_length=50, null=True)
    author_name = models.CharField(blank=True, max_length=50, null=True)
    author_url = models.TextField(blank=True, null=True)
    is_operational = models.BooleanField(default=True)
    uses_docker = models.NullBooleanField(default=True)
    docker_privileged = models.NullBooleanField(default=False)
    docker_params = django.contrib.postgres.fields.JSONField(default=dict, null=True)
    error_mapping = django.contrib.postgres.fields.JSONField(default=dict, null=True)
    trigger_rule = models.ForeignKey('trigger.TriggerRule', blank=True, null=True, on_delete=models.PROTECT)
    priority = models.IntegerField(default=100)
    timeout = models.IntegerField(default=1800, null=True)
    cpus_required = models.FloatField(default=1.0, null=True)
    mem_const_required = models.FloatField(default=64.0, null=True)
    mem_mult_required = models.FloatField(default=0.0, null=True)
    shared_mem_required = models.FloatField(default=0.0, null=True)
    disk_out_const_required = models.FloatField(default=64.0, null=True)
    disk_out_mult_required = models.FloatField(default=0.0, null=True)
    custom_resources = django.contrib.postgres.fields.JSONField(default=dict, null=True)

    objects = JobTypeManager()

    def convert_custom_resources(self):
        """Takes the raw custom_resources dict and performs the Scale version conversion on it so that the REST API
        always returns the latest version of the JSON schema

        :returns: The custom resources dict converted to the latest version of the JSON schema
        :rtype: dict
        """

        return self.get_custom_resources().get_dict()

    def get_custom_resources(self):
        """Returns the custom resources required for jobs of this type

        :returns: The custom resources
        :rtype: :class:`node.resources.json.resources.Resources`
        """

        return Resources(self.custom_resources)

    def get_job_interface(self):
        """Returns the interface for running jobs of this type

        :returns: The job interface for this type
        :rtype: :class:`job.configuration.interface.job_interface.JobInterface` or
                :class:`job.seed.manifest.SeedManifest`
        """

        return JobInterfaceSunset.create(self.manifest)

    def get_job_version(self):
        """Gets the Job version either from field or manifest
        :return: the version
        :rtype: str
        """

        interface = self.get_job_interface()

        version = self.version
        # TODO: Make this the only code path when legacy job types are removed
        if isinstance(interface, SeedManifest):
            version = interface.get_job_version()

        return version


    def get_job_version_array(self, version):
        """Gets the Job version either from field or manifest as an array of integers
           for sorting using the semver package. The result will be an array of length
           4 with the first three being integers containing major,minor and patch version
           numbers. The fourth will be either a None value or if a prerelease value is
           present this function will attempt to convert it into an integer for sorting.
        :keyword version: The version of the job type
        :type version: :class:`django.db.models.CharField`
        :return: the version array
        :rtype: array
        """
        parts = None
        try:
            parts = semver.parse(version)
        except:
            return [0,0,0,0]
        prerelease = None
        if parts['prerelease']:
            # attempt to convert pre-release field to a number for sorting
            # we want a non-null value if there is a pre-release field in version as
            # null values come first when sorting by descending order so we want
            # any prerelease versions to have a non-null value
            prerelease = re.sub("[^0-9]", "", parts['prerelease'])
            try:
                prerelease = int(prerelease)
            except ValueError:
                prerelease = ord(parts['prerelease'][0])
        version_array = [parts['major'], parts['minor'], parts['patch'], prerelease]

        return version_array

    def get_package_version(self):
        """Gets the package version from manifest

        This value is None in legacy job type

        :return: the version
        :rtype: str
        """

        interface = self.get_job_interface()

        version = None
        # TODO: Make this the only code path when legacy job types are removed
        if isinstance(interface, SeedManifest):
            version = interface.get_package_version()

        return version

    def get_category(self):
        """Returns the category for this job type

        # TODO: Remove in v6 in deference to tag access within the manifest
        This is merely a placeholder for the short term to minimize changes associate with Seed migration


        :returns: The category of job type (or first tag in SeedManifest as of v6)
        :rtype: str
        """

        if JobInterfaceSunset.is_seed_dict(self.manifest):
            tags = self.get_job_interface().get_tags()
            if tags:
                return tags[0]

        return self.category

    def get_error_mapping(self):
        """Returns the error mapping for this job type

        :returns: The error mapping
        :rtype: :class:`job.error.mapping.JobErrorMapping`
        """

        # TODO: remove when legacy job types go away
        if not JobInterfaceSunset.is_seed_dict(self.manifest):
            from job.error.mapping import create_legacy_error_mapping
            return create_legacy_error_mapping(self.error_mapping)

        return SeedManifest(self.manifest).get_error_mapping()

    def get_job_configuration(self):
        """Returns the job configuration for this job type

        :returns: The job configuration for this job type
        :rtype: :class:`job.configuration.configuration.JobConfiguration`
        """

        return JobConfigurationV6(config=self.configuration, do_validate=False).get_configuration()

    def get_resources(self):
        """Returns the resources required for jobs of this type

        :returns: The required resources
        :rtype: :class:`node.resources.node_resources.NodeResources`
        """

        # TODO: Remove first block of conditional come v6
        if not JobInterfaceSunset.is_seed_dict(self.manifest):
            resources = Resources(self.custom_resources).get_node_resources()
            resources.remove_resource('cpus')
            resources.remove_resource('mem')
            resources.remove_resource('disk')
            cpus = max(self.cpus_required, MIN_CPUS)
            resources.add(NodeResources([Cpus(cpus)]))
        else:
            interface = self.get_job_interface()
            seed_resources = {}
            # Check all specified resources
            for x in interface.get_scalar_resources():
                name = x['name'].lower()
                # Ensure resource meets minimums set
                seed_resources[name] = max(x['value'], MIN_RESOURCE.get(name, 0.0))

            # Ensure all standard resource minimums are satisfied
            for resource in MIN_RESOURCE:
                if resource not in seed_resources:
                    seed_resources[resource] = MIN_RESOURCE[resource]

            resources = Resources({'resources': seed_resources}).get_node_resources()

        return resources

    def get_secrets_key(self):
        """Returns the reference key for job type secrets stored in the secrets backend.

        :returns: The job_type name and version concatenated
        :rtype: str
        """

        return '-'.join([self.name, self.version]).replace('.', '_')

    def get_v2_configuration_json(self):
        """Returns the job configuration in v2 of the JSON schema

        :returns: The job configuration in v2 of the JSON schema
        :rtype: dict
        """

        return rest_utils.strip_schema_version(convert_config_to_v2_json(self.get_job_configuration()).get_dict())

    def get_v6_configuration_json(self):
        """Returns the job configuration in v6 of the JSON schema

        :returns: The job configuration in v6 of the JSON schema
        :rtype: dict
        """

        return rest_utils.strip_schema_version(convert_config_to_v6_json(self.get_job_configuration()).get_dict())

    def get_cpus_required(self):
        """Either returns field value or pulls from Seed resources

        # TODO remove in v6 in deference to direct exposure of Seed Manifest

        :return: cpus required by job
        :rtype: float
        """

        return self._get_legacy_resource('cpus', self.cpus_required, True)

    def get_mem_const_required(self):
        """Either returns field value or pulls from Seed resources

        # TODO remove in v6 in deference to direct exposure of Seed Manifest

        :return: memory constant required by job
        :rtype: float
        """

        return self._get_legacy_resource('mem', self.mem_const_required, True)

    def get_mem_mult_required(self):
        """Either returns field value or pulls from Seed resources

        # TODO remove in v6 in deference to direct exposure of Seed Manifest

        :return: memory multiplier required by job
        :rtype: float
        """

        return self._get_legacy_resource('mem', self.mem_mult_required, False)

    def get_shared_mem_required(self):
        """Either returns field value or pulls from Seed resources

        # TODO remove in v6 in deference to direct exposure of Seed Manifest

        :return: shared memory required by job
        :rtype: float
        """

        return self._get_legacy_resource('sharedmem', self.shared_mem_required, True)

    def get_disk_out_const_required(self):
        """Either returns field value or pulls from Seed resources

        # TODO remove in v6 in deference to direct exposure of Seed Manifest

        :return: disk constant required by job
        :rtype: float
        """

        return self._get_legacy_resource('disk', self.disk_out_const_required, True)

    def get_disk_out_mult_required(self):
        """Either returns field value or pulls from Seed resources

        # TODO remove in v6 in deference to direct exposure of Seed Manifest

        :return: disk multiplier required by job
        :rtype: float
        """

        return self._get_legacy_resource('disk', self.disk_out_mult_required, False)

    def is_seed_job_type(self):
        """Checks if the JobType object is a Seed job type (True) or legacy job type (False)

        :returns: Whether this job type is legacy or Seed
        :rtype: bool
        """

        if JobInterfaceSunset.is_seed_dict(self.manifest):
            return True
        return False

    def natural_key(self):
        """Django method to define the natural key for a job type as the
        combination of name and version

        :returns: A tuple representing the natural key
        :rtype: tuple(string, string)
        """
        return self.name, self.version

    def populate_from_manifest(self, manifest):
        """Set job type fields with values from given seed manifest

        :param manifest: The Seed Manifest defining the interface for running a job of this type
        :type manifest: :class:`job.seed.manifest.SeedManifest`
        """

        self.title = manifest.get_title()
        self.description = manifest.get_description()
        self.author_name = manifest.get_maintainer().get('name')
        self.author_url = manifest.get_maintainer().get('url')
        self.manifest = manifest.get_dict()

    def _get_legacy_resource(self, key, legacy_field, is_value):
        """Helper function to support bridging v5 / v6 storage of resources

        # TODO: remove in v6 in deference to direct exposure of Seed Manifest

        :param key: the lower-case key name for the resource
        :param legacy_field: the legacy field value to use
        :param is_value: if True lookup `value` key otherwise `inputMultiplier` key
        :return:
        """
        value = 0.0

        if JobInterfaceSunset.is_seed_dict(self.manifest):
            for resource in JobInterfaceSunset.create(self.manifest).get_scalar_resources():
                if key in resource['name'].lower():
                    value = resource.get('value' if is_value else 'inputMultiplier', 0.0)
                    break
        else:
            value = legacy_field

        return value

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
        new_rev.manifest = job_type.manifest
        new_rev.docker_image = job_type.docker_image
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

    def get_revision(self, job_type_name, job_type_version, revision_num):
        """Returns the revision (with populated job_type model) for the given job type and revision number

        :param job_type_name: The name of the job type
        :type job_type_name: string
        :param job_type_version: The version of the job type
        :type job_type_version: string
        :param revision_num: The revision number
        :type revision_num: int
        :returns: The revision
        :rtype: :class:`job.models.JobTypeRevision`
        """

        qry = self.select_related('job_type')
        return qry.get(job_type__name=job_type_name, job_type__version=job_type_version, revision_num=revision_num)

    def get_revisions(self, revision_tuples):
        """Returns a dict that maps revision ID to job type revision for the job type revisions that match the
        given values. Each revision model will have its related job type model populated.

        :param revision_tuples: A list of tuples (job type name, job type version, revision num) for additional
            revisions to return
        :type revision_tuples: list
        :returns: The revisions stored by revision ID
        :rtype: dict
        """

        revisions = {}
        qry_filter = None
        for revision_tuple in revision_tuples:
            f = Q(job_type__name=revision_tuple[0], job_type__version=revision_tuple[1], revision_num=revision_tuple[2])
            if qry_filter:
                qry_filter = qry_filter | f
            else:
                qry_filter = f
        for rev in self.select_related('job_type').filter(qry_filter):
            revisions[rev.id] = rev
        return revisions

    def get_job_type_revisions_v6(self, name, version, order=None):
        """Returns a list of the versions of the job type with the given name

        :param name: Name of the job type
        :type name: string
        :param version: The version of the job type.
        :type version: string
        :param order: A list of fields to control the sort order.
        :type order: [string]
        :returns: The list of job type revisions that match the given parameters.
        :rtype: [:class:`job.models.JobTypeRevision`]
        """

        # Attempt to get the job type
        job_type = JobType.objects.all().get(name=name, version=version)

        # Fetch a list of job types
        job_type_revisions = JobTypeRevision.objects.all()

        job_type_revisions = job_type_revisions.filter(job_type=job_type.id)

        # Apply sorting
        if order:
            job_type_revisions = job_type_revisions.order_by(*order)
        else:
            job_type_revisions = job_type_revisions.order_by('last_modified')

        return job_type_revisions

    def get_details_v6(self, name, version, revision_num):
        """Returns the job type revision for the given name, version and revision number
        with all detail fields included.

        :param name: The name of the job type.
        :type name: string
        :param version: The version of the job type.
        :type version: string
        :param revision_num: The revision number of the job type revision.
        :type revision_num: int
        :returns: The job type revision with all detail fields included.
        :rtype: :class:`job.models.JobTypeRevision`
        """

        # Attempt to get the job type
        job_type = JobType.objects.all().get(name=name, version=version)

        # Attempt to get the job type revision
        job_type_rev = JobTypeRevision.objects.all().get(job_type=job_type.id, revision_num=revision_num)

        return job_type_rev

class JobTypeRevision(models.Model):
    """Represents a revision of a job type. New revisions are created when the manifest of a job type changes. Any
    inserts of a job type revision model requires obtaining a lock using select_for_update() on the corresponding job
    type model.

    :keyword job_type: The job type for this revision
    :type job_type: :class:`django.db.models.ForeignKey`
    :keyword revision_num: The number for this revision, starting at one
    :type revision_num: :class:`django.db.models.IntegerField`
    :keyword manifest: The JSON seed manifest for this revision of the job type (previously interface)
    :type manifest: :class:`django.contrib.postgres.fields.JSONField`
    :keyword created: When this revision was created
    :type created: :class:`django.db.models.DateTimeField`
    """

    job_type = models.ForeignKey('job.JobType', on_delete=models.PROTECT)
    revision_num = models.IntegerField()
    manifest = django.contrib.postgres.fields.JSONField(default=dict)
    docker_image = models.TextField(default='')
    created = models.DateTimeField(auto_now_add=True)

    objects = JobTypeRevisionManager()

    def get_input_interface(self):
        """Returns the input interface for this revision

        :returns: The input interface for this revision
        :rtype: :class:`data.interface.interface.Interface`
        """

        if JobInterfaceSunset.is_seed_dict(self.manifest):
            return SeedManifest(self.manifest, do_validate=False).get_input_interface()

        # TODO: This can be removed when support for legacy job types is removed
        interface = Interface()
        for input_dict in self.manifest['input_data']:
            media_types = input_dict['media_types'] if 'media_types' in input_dict else []
            required = input_dict['required'] if 'required' in input_dict else True
            if input_dict['type'] == 'file':
                param = FileParameter(input_dict['name'], media_types, required, False)
                interface.add_parameter(param)
            elif input_dict['type'] == 'files':
                param = FileParameter(input_dict['name'], media_types, required, True)
                interface.add_parameter(param)
            elif input_dict['type'] == 'property':
                interface.add_parameter(JsonParameter(input_dict['name'], 'string', required))
        return interface

    def get_output_interface(self):
        """Returns the output interface for this revision

        :returns: The output interface for this revision
        :rtype: :class:`data.interface.interface.Interface`
        """

        if JobInterfaceSunset.is_seed_dict(self.manifest):
            return SeedManifest(self.manifest, do_validate=False).get_output_interface()

        # TODO: This can be removed when support for legacy job types is removed
        interface = Interface()
        for output_dict in self.manifest['output_data']:
            media_types = output_dict['media_types'] if 'media_types' in output_dict else []
            required = output_dict['required'] if 'required' in output_dict else True
            if output_dict['type'] == 'file':
                param = FileParameter(output_dict['name'], media_types, required, False)
                interface.add_parameter(param)
            elif output_dict['type'] == 'files':
                param = FileParameter(output_dict['name'], media_types, required, True)
                interface.add_parameter(param)
            elif output_dict['type'] == 'property':
                interface.add_parameter(JsonParameter(output_dict['name'], 'string', required))
        return interface

    def get_job_interface(self):
        """Returns the job type interface for this revision

        :returns: The job type interface for this revision
        :rtype: :class:`job.configuration.interface.job_interface.JobInterface` or `job.seed.manifest.SeedManifest`
        """

        return JobInterfaceSunset.create(self.manifest)

    def natural_key(self):
        """Django method to define the natural key for a job type revision as the combination of job type and revision
        number

        :returns: A tuple representing the natural key
        :rtype: tuple(string, int)
        """

        return self.job_type, self.revision_num

    class Meta(object):
        """meta information for the db"""
        db_table = 'job_type_revision'
        unique_together = ('job_type', 'revision_num')


class TaskUpdate(models.Model):
    """Represents a status update received for a task

    :keyword job_exe: The job execution that the task belongs to
    :type job_exe: :class:`django.db.models.ForeignKey`
    :keyword task_id: The task ID
    :type task_id: :class:`django.db.models.CharField`
    :keyword status: The status of the task
    :type status: :class:`django.db.models.CharField`

    :keyword timestamp: When the status update occurred (may be None)
    :type timestamp: :class:`django.db.models.DateTimeField`
    :keyword source: An optional source of the task status update
    :type source: :class:`django.db.models.CharField`
    :keyword reason: An optional reason for the task status update
    :type reason: :class:`django.db.models.CharField`
    :keyword message: An optional message related to the task status update
    :type message: :class:`django.db.models.TextField`

    :keyword created: When the task update was saved in the database
    :type created: :class:`django.db.models.DateTimeField`
    """

    job_exe = models.ForeignKey('job.JobExecution', on_delete=models.PROTECT)
    task_id = models.CharField(max_length=250)
    status = models.CharField(max_length=250)

    timestamp = models.DateTimeField(blank=True, null=True)
    source = models.CharField(blank=True, max_length=250, null=True)
    reason = models.CharField(blank=True, max_length=250, null=True)
    message = models.TextField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        """Meta information for the database"""
        db_table = 'task_update'

class JobTypeTagManager(models.Manager):
    """Provides additional methods for handling job type tags
    """

    def create_job_type_tags(self, job_type, tags):
        """Creates a set of job type tags and saves them in the database

        :param job_type: The job type
        :type job_type: :class:`job.models.JobType`
        :param tag: The tags of the job type image
        :type tag: list
        :returns: The new job type tags
        :rtype: list
        """

        job_type_tags = []
        for tag in tags:
            # Create the new job type tag
            job_type_tag = JobTypeTag()
            job_type_tag.job_type = job_type
            job_type_tag.tag = tag
            job_type_tags.append(job_type_tag)

        if job_type_tags:
            self.bulk_create(job_type_tags)

        return job_type_tags

    def clear_job_type_tags(self, job_type_id):
        """Removes all job type tag objects for the specified job type. Useful when updating the revision and
        repopulating with new tags

        :param job_type_id: The job type ID to remove tags for
        :type job_type_id: int
        """

        self.filter(job_type_id=job_type_id).delete()

    def update_job_type_tags(self, job_type, manifest):
        """Updates the tags for the given job type

        :param job_type: The job type
        :type job_type: :class:`job.models.JobType`
        :param manifest: The Seed manifest for the job type
        :type manifest: :class:`job.seed.manifest.SeedManifest`
        """

        tags = manifest.get_tags()
        if tags is None:
            tags = []

        self.clear_job_type_tags(job_type.id)
        self.create_job_type_tags(job_type, tags)


class JobTypeTag(models.Model):
    """Stores a job type and tag combination

    :keyword job type: The job type
    :type name: :class:`django.db.models.ForeignKey`
    :keyword tag: The tag associated with the job type
    :type tag: :class:`django.db.models.CharField`
    """

    job_type = models.ForeignKey('job.JobType', on_delete=models.PROTECT)
    tag = models.CharField(db_index=True, max_length=50)

    objects = JobTypeTagManager()

    class Meta(object):
        """meta information for the db"""
        db_table = 'job_type_tag'
