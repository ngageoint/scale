"""Defines the command that performs the pre-job steps"""
from __future__ import unicode_literals

import json
import logging
import os
import sys

from django.core.management.base import BaseCommand
from django.utils.text import get_valid_filename
from django.utils.timezone import now

from error.exceptions import ScaleError, get_error_by_exception
from job.data.job_data import JobData
from data.data.value import FileValue, JsonValue
from job.execution.container import SCALE_INPUT_METADATA_PATH
from job.models import JobExecution
from storage.brokers.broker import FileUpload
from storage.models import ScaleFile, Workspace
from storage.serializers import ScaleFileDetailsSerializerV6 as serialize
from util.retry import retry_database_query


logger = logging.getLogger(__name__)


GENERAL_FAIL_EXIT_CODE = 1


class Command(BaseCommand):
    """Command that performs the pre-job steps for a job execution
    """

    help = 'Performs the pre-job steps for a job execution'

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the command.
        """

        job_id = int(os.environ.get('SCALE_JOB_ID'))
        exe_num = int(os.environ.get('SCALE_EXE_NUM'))
        logger.info('Command starting: scale_pre_steps - Job ID: %d, Execution Number: %d', job_id, exe_num)
        try:
            job_exe = self._get_job_exe(job_id, exe_num)

            job_interface = job_exe.job_type.get_job_interface()
            exe_config = job_exe.get_execution_configuration()
            logger.info('Validating mounts...')
            job_interface.validate_populated_mounts(exe_config)
            logger.info('Validating settings...')
            job_interface.validate_populated_settings(exe_config)
            logger.info('Validating outputs and workspaces...')
            job_interface.validate_workspace_for_outputs(exe_config)

            self._generate_input_metadata(job_exe)

            job_data = job_exe.job.get_job_data()
            job_data = JobData(job_data.get_dict())
            logger.info('Setting up input files...')

            download_files = True
            if job_exe.job_type.name == "scale-fork-jobs":
                download_files = False
            job_interface.perform_pre_steps(job_data, download_files)

            logger.info('Ready to execute job: %s', exe_config.get_args('main'))
        except ScaleError as err:
            err.log()
            sys.exit(err.exit_code)
        except Exception as ex:
            exit_code = GENERAL_FAIL_EXIT_CODE
            err = get_error_by_exception(ex.__class__.__name__)
            if err:
                err.log()
                exit_code = err.exit_code
            else:
                logger.exception('Error performing pre-job steps')

            sys.exit(exit_code)

        logger.info('Command completed: scale_pre_steps')

    @retry_database_query
    def _get_job_exe(self, job_id, exe_num):
        """Returns the job execution for the ID with its related job and job type models

        :param job_id: The job ID
        :type job_id: int
        :param exe_num: The execution number
        :type exe_num: int
        :returns: The job execution model
        :rtype: :class:`job.models.JobExecution`
        """

        return JobExecution.objects.get_job_exe_with_job_and_job_type(job_id, exe_num)

    def _generate_input_metadata(self, job_exe):
        """Generate the input metadata file for the job execution

        :param job_exe: The job_exe model
        :type job_exe: `job.models.JobExecution`
        """

        # Generate input metadata dict
        input_metadata = {}
        config = job_exe.get_execution_configuration()
        if 'input_files' in config.get_dict():
            input_metadata['JOB'] = {}
            input_data = job_exe.job.get_input_data()
            for i in input_data.values.keys():
                if type(input_data.values[i]) is JsonValue:
                    input_metadata['JOB'][i] = input_data.values[i].value
                elif type(input_data.values[i]) is FileValue:
                    input_metadata['JOB'][i] = [serialize(ScaleFile.objects.get_details(file_id=f)).data for f in
                                                input_data.values[i].file_ids]
        if job_exe.recipe_id and job_exe.recipe.has_input():
            input_metadata['RECIPE'] = {}
            input_data = job_exe.recipe.get_input_data()
            for i in input_data.values.keys():
                if type(input_data.values[i]) is JsonValue:
                    input_metadata['RECIPE'][i] = input_data.values[i].value
                elif type(input_data.values[i]) is FileValue:
                    input_metadata['RECIPE'][i] = [serialize(ScaleFile.objects.get_details(file_id=f)).data for f in
                                                   input_data.values[i].file_ids]

        logger.debug("Scale Input Metadata Manifest Generated:")
        log_str = json.dumps(input_metadata, sort_keys=True, indent=4, separators=(',', ': '))
        logger.debug(log_str)

        try:
            with open(SCALE_INPUT_METADATA_PATH, 'w+') as metadata_file:
                json.dump(input_metadata, metadata_file)
        except Exception as ex:
            logger.exception('Error dumping input metadata manifest to file %s: %s' % (SCALE_INPUT_METADATA_PATH, ex))

    def _calculate_remote_path(self, job_exe):
        """Returns the remote path for storing the manifest

        :param job_exe: The job execution model (with related job and job_type fields) that is storing the files
        :type job_exe: :class:`job.models.JobExecution`
        :returns: The remote path for storing the manifest
        :rtype: str
        """

        remote_path = ''
        if job_exe.job.recipe:
            recipe = job_exe.job.recipe
            recipe_type_path = get_valid_filename(recipe.recipe_type.name)
            recipe_version_path = get_valid_filename(recipe.recipe_type.revision_num)
            remote_path = os.path.join(remote_path, 'recipes', recipe_type_path, recipe_version_path)
        job_type_path = get_valid_filename(job_exe.job.job_type.name)
        job_version_path = get_valid_filename(job_exe.job.job_type.version)
        remote_path = os.path.join(remote_path, 'jobs', job_type_path, job_version_path)

        the_date = now()
        year_dir = str(the_date.year)
        month_dir = '%02d' % the_date.month
        day_dir = '%02d' % the_date.day
        return os.path.join(remote_path, year_dir, month_dir, day_dir, 'job_exe_%i' % job_exe.id)
