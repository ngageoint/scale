"""Defines the class that performs the Scale database update"""
from __future__ import unicode_literals

import logging

from django.db import connection, transaction

from batch.configuration.configuration import BatchConfiguration
from batch.models import Batch
from job.deprecation import JobInterfaceSunset, JobDataSunset
from job.execution.tasks.json.results.task_results import TaskResults
from job.models import Job, JobExecution, JobExecutionEnd, JobExecutionOutput, JobType, JobTypeRevision, TaskUpdate
from job.seed.manifest import SeedManifest
from recipe.models import Recipe
from util.exceptions import TerminatedCommand
from util.parse import datetime_to_string


logger = logging.getLogger(__name__)

INTERFACE_NAME_COUNTER = 0

def get_unique_name(name):
    global INTERFACE_NAME_COUNTER
    new_name = '%s_%d' % (name, INTERFACE_NAME_COUNTER)
    new_name = new_name.replace(' ', '_')
    INTERFACE_NAME_COUNTER += 1
    return new_name

class DatabaseUpdater(object):
    """This class manages the Scale database update. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._running = True
        self._updated_job_exe = 0
        self._total_job_exe = 0
        self._updated_job = 0
        self._total_job = 0
        self._current_recipe_id = None
        self._updated_recipe = 0
        self._total_recipe = 0
        self._current_batch_id = None
        self._updated_batch = 0
        self._total_batch = 0
        self._total_recipe_definition = 0
        self._update_recipe_definition = 0
        self._current_recipe_definition_id = None
        self._current_job_type_id = None
        self._updated_job_type = 0
        self._total_job_type = 0

    def update(self):
        """Runs the database update
        """

        # Converting job execution models
        self._perform_update_init()
        while True:
            if not self._running:
                raise TerminatedCommand()

            if self._updated_job_exe >= self._total_job_exe:
                break
            self._perform_update_iteration()

        # Removing job execution duplicates
        self._perform_job_exe_dup_init()
        while True:
            if not self._running:
                raise TerminatedCommand()

            if self._updated_job >= self._total_job:
                break
            self._perform_job_exe_dup_iteration()

        # Populating new recipe fields in job models
        self._perform_recipe_field_init()
        while True:
            if not self._running:
                raise TerminatedCommand()

            if self._updated_recipe >= self._total_recipe:
                break
            self._perform_recipe_field_iteration()

        # Populating new batch fields in job and recipe models
        self._perform_batch_field_init()
        while True:
            if not self._running:
                raise TerminatedCommand()

            if self._updated_batch >= self._total_batch:
                break
            self._perform_batch_field_iteration()

        # Updating legacy job type interfaces to seed manifests
        self._perform_job_type_manifest_init()
        while True:
            if not self._running:
                raise TerminatedCommand()

            if self._updated_job_type >= self._total_job_type:
                break
            self._perform_job_type_manifest_iteration()


    def stop(self):
        """Informs the database updater to stop running
        """

        logger.info('Scale database updater has been told to stop')
        self._running = False


    def _perform_job_type_manifest_init(self):
        """Performs any initialization piece of the updating job type interfaces
        """

        logger.info('Scale is now updating legacy job type interfaces to compliant seed manifests')
        logger.info('Counting the number of job types...')
        self._total_job_type = JobType.objects.all().count()
        logger.info('Found %d job types that need to be done', self._total_job_type)

    def _perform_job_type_manifest_iteration(self):
        """Performs a single iteration of updating job type interfaces
        """

        # Get job type ID
        jt_qry = JobType.objects.all()
        if self._current_job_type_id:
            jt_qry = jt_qry.filter(id__gt=self._current_job_type_id)
        for jt in jt_qry.order_by('id').only('id')[:1]:
            jt_id = jt.id
            break

        jt = JobType.objects.get(pk=jt_id)
        if not JobInterfaceSunset.is_seed_dict(jt.manifest):
            jt.is_active = False
            jt.is_paused = True
            old_name_version = jt.name + ' ' + jt.version
            jt.name = 'legacy-' + jt.name.replace('_', '-')

            if not jt.manifest:
                jt.manifest = {}

            input_files = []
            input_json = []
            output_files = []
            global INTERFACE_NAME_COUNTER
            INTERFACE_NAME_COUNTER = 0
            for input in jt.manifest.get('input_data', []):
                type = input.get('type', '')
                if 'file' not in type:
                    json = {}
                    json['name'] = get_unique_name(input.get('name'))
                    json['type'] = 'string'
                    json['required'] = input.get('required', True)
                    input_json.append(json)
                    continue
                file = {}
                file['name'] = get_unique_name(input.get('name'))
                file['required'] = input.get('required', True)
                file['partial'] = input.get('partial', False)
                file['mediaTypes'] = input.get('media_types', [])
                file['multiple'] = (type == 'files')
                input_files.append(file)

            for output in jt.manifest.get('output_data', []):
                type = output.get('type', '')
                file = {}
                file['name'] = get_unique_name(output.get('name'))
                file['required'] = output.get('required', True)
                file['mediaType'] = output.get('media_type', '')
                file['multiple'] = (type == 'files')
                file['pattern'] = "*.*"
                output_files.append(file)

            mounts = []
            for mount in jt.manifest.get('mounts', []):
                mt = {}
                mt['name'] = get_unique_name(mount.get('name'))
                mt['path'] = mount.get('path')
                mt['mode'] = mount.get('mode', 'ro')
                mounts.append(mt)

            settings = []
            for setting in jt.manifest.get('settings', []):
                s = {}
                s['name'] = get_unique_name(setting.get('name'))
                s['secret'] = setting.get('secret', False)
                settings.append(s)
            for var in jt.manifest.get('env_vars', []):
                s = {}
                name = get_unique_name(var.get('name'))
                name = 'ENV_' + name
                s['name'] = name
                settings.append(s)

            new_manifest = {
                'seedVersion': '1.0.0',
                'job': {
                    'name': jt.name,
                    'jobVersion': '0.0.0',
                    'packageVersion': '1.0.0',
                    'title': 'Legacy Title',
                    'description': 'legacy job type: ' + old_name_version,
                    'tags': [],
                    'maintainer': {
                      'name': 'Legacy',
                      'email': 'jdoe@example.com'
                    },
                    'timeout': 3600,
                    'interface': {
                      'command': jt.manifest.get('command', ''),
                      'inputs': {
                        'files': input_files,
                        'json': input_json
                      },
                      'outputs': {
                        'files': output_files,
                        'json': []
                      },
                      'mounts': mounts,
                      'settings': settings
                    },
                    'resources': {
                      'scalar': [
                        { 'name': 'cpus', 'value': 1.0 },
                        { 'name': 'mem', 'value': 1024.0 },
                        { 'name': 'disk', 'value': 1000.0, 'inputMultiplier': 4.0 }
                      ]
                    },
                    'errors': []
                  }
                }
            jt.manifest = new_manifest
            SeedManifest(jt.manifest, do_validate=True)
            jt.save()
            for jtr in JobTypeRevision.objects.filter(job_type_id=jt.id).iterator():
                jtr.manifest = jt.manifest
                jtr.save()


        self._current_job_type_id = jt_id
        self._updated_job_type += 1
        if self._updated_job_type > self._total_job_type:
            self._updated_job_type = self._total_job_type
        percent = (float(self._updated_job_type) / float(self._total_job_type)) * 100.00
        logger.info('Completed %s of %s job types (%.1f%%)', self._updated_job_type, self._total_job_type, percent)