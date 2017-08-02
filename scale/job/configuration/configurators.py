"""Defines the classes that handle processing job and execution configuration"""
from __future__ import unicode_literals

import os

from job.configuration.input_file import InputFile
from job.configuration.json.execution.exe_config import ExecutionConfiguration
from job.execution.container import SCALE_JOB_EXE_INPUT_PATH, SCALE_JOB_EXE_OUTPUT_PATH


def normalize_env_var_name(name):
    """Returns a normalized version of the given string name so it can be used as the name of an environment variable

    :param name: The string name to normalize
    :type name: string
    :returns: The normalized environment variable name
    :rtype: string
    """

    return name.replace('-', '_').upper()


class QueuedExecutionConfigurator(object):
    """Configurator that creates execution configurations when a job execution is queued
    """

    def __init__(self, input_files):
        """Creates a QueuedExecutionConfigurator for a set of input files. Each scale_file model must have its related
        workspace field populated.

        :param input_files: The dict of scale_file models stored by ID
        :type input_files: dict
        """

        self._input_files = input_files

    def configure_queued_job(self, job):
        """Creates and returns an execution configuration for the given queued job. The given job model should have its
        related job_type and job_type_rev models populated.

        :param job: The queued job model
        :type job: :class:`job.models.Job`
        :returns: The execution configuration for the queued job
        :rtype: :class:`job.configuration.json.execution.exe_config.ExecutionConfiguration`
        """

        config = ExecutionConfiguration()
        data = job.get_job_data()
        input_files_dict = self._create_input_file_dict(data)
        config.set_input_files(input_files_dict)

        # Set up env vars for job's input data
        env_vars = {}
        # TODO: refactor this to use JobData method after Seed upgrade
        for data_input in data.get_dict()['input_data']:
            input_name = data_input['name']
            env_var_name = normalize_env_var_name(input_name)
            if 'value' in data_input:
                env_vars[env_var_name] = data_input['value']
            if 'file_id' in data_input:
                input_file = input_files_dict[input_name][0]
                file_name = os.path.basename(input_file.workspace_path)
                if input_file.local_file_name:
                    file_name = input_file.local_file_name
                env_vars[env_var_name] = os.path.join(SCALE_JOB_EXE_INPUT_PATH, input_name, file_name)
            elif 'file_ids' in data_input:
                env_vars[env_var_name] = os.path.join(SCALE_JOB_EXE_INPUT_PATH, input_name)

        # Add env var for output directory
        # TODO: original output dir can be removed when Scale only supports Seed-based job types
        env_vars['job_output_dir'] = SCALE_JOB_EXE_OUTPUT_PATH  # Original output directory
        env_vars['OUTPUT_DIR'] = SCALE_JOB_EXE_OUTPUT_PATH  # Seed output directory

        # Create main task with command args and env vars for input data
        config.create_tasks(['main'])
        config.add_to_task('main', args=job.get_job_interface().get_command_args(), env_vars=env_vars)

        return config

    def _create_input_file_dict(self, job_data):
        """Creates the dict storing lists of input files by input name

        :param job_data: The job data
        :type job_data: :class:`job.configuration.data.job_data.JobData`
        :returns: A dict where input name maps to lists of input files
        :rtype: dict
        """

        files_dict = {}

        for input_name, file_ids in job_data.get_input_file_ids_by_input().items():
            file_list = []
            file_names = set()
            for file_id in file_ids:
                scale_file_model = self._input_files[file_id]
                input_file = InputFile(scale_file_model)
                # Check for file name collision and use Scale file ID to ensure names are unique
                file_name = scale_file_model.file_name
                if file_name in file_names:
                    file_name = '%d.%s' % (scale_file_model.id, file_name)
                    input_file.local_file_name = file_name
                file_names.add(file_name)
                file_list.append(input_file)
            files_dict[input_name] = file_list

        return files_dict
