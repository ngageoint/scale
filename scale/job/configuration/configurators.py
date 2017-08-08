"""Defines the classes that handle processing job and execution configuration"""
from __future__ import unicode_literals

import math
import os

from job.configuration.docker_param import DockerParameter
from job.configuration.input_file import InputFile
from job.configuration.json.execution.exe_config import ExecutionConfiguration
from job.configuration.volume import MODE_RW
from job.configuration.workspace import Workspace
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

        # Add input file meta-data
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

        # Add any workspaces needed if this is a system job
        workspaces = {}
        if job.job_type.is_system:
            workspaces = QueuedExecutionConfigurator._system_task_workspaces(job)

        # Add env var for output directory
        # TODO: original output dir can be removed when Scale only supports Seed-based job types
        env_vars['job_output_dir'] = SCALE_JOB_EXE_OUTPUT_PATH  # Original output directory
        env_vars['OUTPUT_DIR'] = SCALE_JOB_EXE_OUTPUT_PATH  # Seed output directory

        # Create main task with fields populated from input data
        config.create_tasks(['main'])
        config.add_to_task('main', args=job.get_job_interface().get_command_args(), env_vars=env_vars,
                           workspaces=workspaces)

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

    @staticmethod
    def _system_task_workspaces(job):
        """Returns any workspaces needed for the main task if this job is a system job. The given job model should have
        its related job_type and job_type_rev models populated.

        :param job: The queued job model
        :type job: :class:`job.models.Job`
        :returns: A dict where workspaces are stored by name
        :rtype: dict
        """

        workspaces = {}
        data = job.get_job_data()

        if job.job_type.name == 'scale-ingest':
            workspace_name = None
            new_workspace_name = None
            prop_dict = data.get_property_values(['Ingest ID', 'workspace', 'new_workspace'])
            if 'workspace' in prop_dict:
                workspace_name = prop_dict['workspace']
                if 'new_workspace' in prop_dict:
                    new_workspace_name = prop_dict['new_workspace']
            else:
                # Old ingest jobs do not have the workspace(s) in their data, will need to query ingest model
                if 'Ingest ID' in prop_dict:
                    ingest_id = int(prop_dict['Ingest ID'])
                    from ingest.models import Ingest
                    ingest = Ingest.objects.select_related('workspace', 'new_workspace').get(id=ingest_id)
                    workspace_name = ingest.workspace.name
                    new_workspace_name = ingest.new_workspace.name
            if workspace_name:
                workspaces[workspace_name] = Workspace(workspace_name, MODE_RW)
            if new_workspace_name:
                workspaces[new_workspace_name] = Workspace(new_workspace_name, MODE_RW)

        return workspaces


class ScheduledExecutionConfigurator(object):
    """Configurator that handles execution configurations when a job execution is scheduled
    """

    def __init__(self, workspaces):
        """Creates a ScheduledExecutionConfigurator

        :param workspaces: The dict of workspace models stored by name
        :type workspaces: dict
        """

        self._workspaces = workspaces

    def configure_scheduled_job(self, job_exe, job_type, interface):
        """Configures the JSON configuration field for the given scheduled job execution. The given job_exe and job_type
        models will not have any related fields populated. The execution configuration in the job_exe model will have
        all secret values replaced with '*****' so that it is safe to be stored in the database. Another copy of this
        configuration will be returned that has the actual secret values populated and can be used for actual
        scheduling.

        :param job_exe: The job execution model being scheduled
        :type job_exe: :class:`job.models.JobExecution`
        :param job_type: The job type model
        :type job_type: :class:`job.models.JobType`
        :param interface: The job interface
        :type interface: :class:`job.configuration.interface.job_interface.JobInterface`
        :returns: A copy of the configuration containing secret values
        :rtype: :class:`job.configuration.json.execution.exe_config.ExecutionConfiguration`
        """

        config = job_exe.get_execution_configuration()

        # Set shared memory if required by this job type
        shared_mem = job_type.shared_mem_required
        if shared_mem > 0:
            config.add_to_task('main', docker_params=[DockerParameter('shm-size', '%dm' % int(math.ceil(shared_mem)))])

        # TODO: add mounts/volumes to main task (interface, job_type.job_config)

        # TODO: check for system vs non-system job and add DB settings, IO mounts, and workspaces as needed
        # TODO: add workspaces from populate_job_data()
        # TODO: move output dir env var (setting?) to here
        # TODO: this includes system jobs like strike and scan - figure out if these can be resolved now (like ingest)

        # TODO: apply resource env vars to all tasks (including shared mem) (add resources to task JSONs)
        # TODO: convert workspaces to volumes (add in workspace volume names) for all tasks
        # TODO: apply logging docker params to all tasks

        # TODO: make copy of this configuration
        config_with_secrets = None
        # TODO: populate settings in both (copy with secrets, this without) (provide DB settings values)
        # TODO: convert settings to env vars in both
        # TODO: add env vars from interface until this feature goes away
        # TODO: convert volumes and env vars to docker params in both
        # TODO: add docker params from job type until this feature gets removed
        return config_with_secrets
