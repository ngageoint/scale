"""Defines utility methods for testing jobs and job types"""
from __future__ import unicode_literals
from __future__ import absolute_import

import copy
import datetime

import django.utils.timezone as timezone

import error.test.utils as error_test_utils
import trigger.test.utils as trigger_test_utils
from job.execution.configuration.configurators import QueuedExecutionConfigurator, ScheduledExecutionConfigurator
from job.configuration.data.exceptions import InvalidConnection
from job.configuration.json.job_config_v6 import convert_config_to_v6_json, JobConfigurationV6
from job.execution.configuration.json.exe_config import ExecutionConfiguration
from job.configuration.results.job_results import JobResults
from job.execution.job_exe import RunningJobExecution
from job.execution.tasks.json.results.task_results import TaskResults
from job.models import Job, JobExecution, JobExecutionEnd, JobExecutionOutput, JobInputFile, JobType, JobTypeRevision, TaskUpdate
from job.seed.manifest import SeedManifest
from job.tasks.update import TaskStatusUpdate
from node.test import utils as node_utils
import storage.test.utils as storage_test_utils
from storage.models import ScaleFile, Workspace
from trigger.handler import TriggerRuleHandler, register_trigger_rule_handler


JOB_TYPE_NAME_COUNTER = 1
JOB_TYPE_VERSION_COUNTER = 1
JOB_TYPE_CATEGORY_COUNTER = 1

RULE_EVENT_COUNTER = 1

COMPLETE_MANIFEST = {
    'seedVersion': '1.0.0',
    'job': {
        'name': 'my-job',
        'jobVersion': '1.0.0',
        'packageVersion': '1.0.0',
        'title': 'My first job',
        'description': 'Reads an HDF5 file and outputs two png images, a CSV and manifest containing cell_count',
        'tags': [ 'hdf5', 'png', 'csv', 'image processing' ],
        'maintainer': {
          'name': 'John Doe',
          'organization': 'E-corp',
          'email': 'jdoe@example.com',
          'url': 'http://www.example.com',
          'phone': '666-555-4321'
        },
        'timeout': 3600,
        'interface': {
          'command': '${INPUT_FILE} ${OUTPUT_DIR} ${VERSION}',
          'inputs': {
            'files': [
              {
                'name': 'INPUT_FILE',
                'required': True,
                'mediaTypes': [
                  'image/x-hdf5-image'
                ],
                'partial': True
              }
            ],
            'json': [
              {
                'name': 'INPUT_JSON',
                'type': 'string',
                'required': True
              }
            ]
          },
          'outputs': {
            'files': [
              {
                'name': 'output_file_pngs',
                'mediaType': 'image/png',
                'multiple': True,
                'pattern': 'outfile*.png'
              },
              {
                'name': 'output_file_csv',
                'mediaType': 'text/csv',
                'pattern': 'outfile*.csv',
                'required': False
              }
            ],
            'json': [
              {
                'name': 'cell_count',
                'key': 'cellCount',
                'type': 'integer'
              },
              {
                'name': 'dummy',
                'type': 'integer',
                'required': False
              }
            ]
          },
          'mounts': [
            {
              'name': 'MOUNT_PATH',
              'path': '/the/container/path',
              'mode': 'ro'
            },
            {
              'name': 'WRITE_PATH',
              'path': '/write',
              'mode': 'rw'
            }
          ],
          'settings': [
            {
              'name': 'VERSION',
              'secret': False
            },
            {
              'name': 'DB_HOST',
              'secret': False
            },
            {
              'name': 'DB_PASS',
              'secret': True
            }
          ]
        },
        'resources': {
          'scalar': [
            { 'name': 'cpus', 'value': 1.0 },
            { 'name': 'mem', 'value': 1024.0 },
            { 'name': 'sharedMem', 'value': 1024.0 },
            { 'name': 'disk', 'value': 1000.0, 'inputMultiplier': 4.0 }
          ]
        },
        'errors': [
          {
            'code': 1,
            'name': 'error-name-one',
            'title': 'Error Name',
            'description': 'Error Description',
            'category': 'data'
          },
          {
            'code': 2,
            'name': 'error-name-two',
            'title': 'Error Name',
            'description': 'Error Description',
            'category': 'job'
          }
        ]
      }
    }

MINIMUM_MANIFEST = {
    'seedVersion': '1.0.0',
    'job': {
        'name': 'my-minimum-job',
        'jobVersion': '1.0.0',
        'packageVersion': '1.0.0',
        'title': 'My first job',
        'description': 'Reads an HDF5 file and outputs two png images, a CSV and manifest containing cell_count',
        'maintainer': {
            'name': 'John Doe',
            'email': 'jdoe@example.com'
        },
        'timeout': 3600
    }
}

def create_clock_rule(name=None, rule_type='CLOCK', event_type=None, schedule='PT1H0M0S', is_active=True):
    """Creates a scale clock trigger rule model for unit testing

    :returns: The trigger rule model
    :rtype: :class:`trigger.models.TriggerRule`
    """

    if not event_type:
        global RULE_EVENT_COUNTER
        event_type = 'TEST_EVENT_%i' % RULE_EVENT_COUNTER
        RULE_EVENT_COUNTER += 1

    config = {
        'version': '1.0',
        'event_type': event_type,
        'schedule': schedule,
    }

    return trigger_test_utils.create_trigger_rule(name=name, trigger_type=rule_type, configuration=config,
                                                  is_active=is_active)


def create_clock_event(rule=None, occurred=None):
    """Creates a scale clock trigger event model for unit testing

    :returns: The trigger event model
    :rtype: :class:`trigger.models.TriggerEvent`
    """

    if not rule:
        rule = create_clock_rule()

    if not occurred:
        occurred = timezone.now()

    event_type = None
    if rule.configuration and 'event_type' in rule.configuration:
        event_type = rule.configuration['event_type']

    return trigger_test_utils.create_trigger_event(trigger_type=event_type, rule=rule, occurred=occurred)


def create_job(job_type=None, event=None, status='PENDING', error=None, input=None, num_exes=1, max_tries=None,
               queued=None, started=None, ended=None, last_status_change=None, priority=100, output=None, job_config=None,
               superseded_job=None, is_superseded=False, superseded=None, input_file_size=10.0, recipe=None, save=True):
    """Creates a job model for unit testing

    :returns: The job model
    :rtype: :class:`job.models.Job`
    """

    if not job_type:
        job_type = create_seed_job_type()
    if not event:
        event = trigger_test_utils.create_trigger_event()
    if not last_status_change:
        last_status_change = timezone.now()
    if num_exes == 0:
        input_file_size = None

    if superseded_job and not superseded_job.is_superseded:
        Job.objects.supersede_jobs([superseded_job.id], timezone.now())
    if is_superseded and not superseded:
        superseded = timezone.now()

    recipe_id = recipe.id if recipe else None
    root_recipe_id = recipe.root_superseded_recipe_id if recipe else None

    job_config = JobConfigurationV6(job_config).get_configuration() if job_config else None

    job_type_rev = JobTypeRevision.objects.get_revision(job_type.name, job_type.version, job_type.revision_num)
    job = Job.objects.create_job_v6(job_type_rev, event_id=event.id, superseded_job=superseded_job, recipe_id=recipe_id,
                                    root_recipe_id=root_recipe_id, job_config=job_config)
    job.priority = priority
    job.input = input
    job.status = status
    job.num_exes = num_exes
    job.max_tries = max_tries if max_tries is not None else job_type.max_tries
    job.queued = queued
    job.started = started
    job.ended = ended
    job.last_status_change = last_status_change
    job.error = error
    job.output = output
    job.is_superseded = is_superseded
    job.superseded = superseded
    job.input_file_size = input_file_size
    if save:
        job.save()
    return job

def create_job_exe(job_type=None, job=None, exe_num=None, node=None, timeout=None, input_file_size=10.0, queued=None,
                   started=None, status='RUNNING', error=None, ended=None, output=None, task_results=None, configuration=None):
    """Creates a job_exe model for unit testing, may also create job_exe_end and job_exe_output models depending on
    status

    :returns: The job_exe model
    :rtype: :class:`job.execution.job_exe.RunningJobExecution`
    """

    when = timezone.now()
    if not job:
        job = create_job(job_type=job_type, status=status, input_file_size=input_file_size)
    else:
        job.num_exes = job.num_exes + 1
        job.save()
    job_type = job.job_type

    job_exe = JobExecution()
    job_exe.job = job
    job_exe.job_type = job_type
    if not exe_num:
        exe_num = job.num_exes
    job_exe.exe_num = exe_num
    job_exe.set_cluster_id('1234', job.id, job_exe.exe_num)
    if not node:
        node = node_utils.create_node()
    job_exe.node = node
    if not timeout:
        timeout = 3600
    job_exe.timeout = timeout
    job_exe.input_file_size = input_file_size
    job_exe.resources = job.get_resources().get_json().get_dict()
    if not configuration:
        configuration = ExecutionConfiguration().get_dict()
    job_exe.configuration = configuration
    if not queued:
        queued = when
    job_exe.queued = queued
    if not started:
        started = when + datetime.timedelta(seconds=1)
    job_exe.started = started
    if job.recipe_id:
        job_exe.recipe = job.recipe
    job_exe.save()

    if status in ['COMPLETED', 'FAILED', 'CANCELED']:
        job_exe_end = JobExecutionEnd()
        job_exe_end.job_exe_id = job_exe.id
        job_exe_end.job = job_exe.job
        job_exe_end.job_type = job_exe.job_type
        job_exe_end.exe_num = job_exe.exe_num
        if not task_results:
            task_results = TaskResults()
        job_exe_end.task_results = task_results.get_dict()
        job_exe_end.status = status
        if status == 'FAILED' and not error:
            error = error_test_utils.create_error()
        job_exe_end.error = error
        job_exe_end.node = node
        job_exe_end.queued = queued
        job_exe_end.started = started
        job_exe_end.seed_started = task_results.get_task_started('main')
        job_exe_end.seed_ended = task_results.get_task_ended('main')
        if not ended:
            ended = started + datetime.timedelta(seconds=1)
        job_exe_end.ended = ended
        job_exe_end.save()

    if status == 'COMPLETED' or output:
        job_exe_output = JobExecutionOutput()
        job_exe_output.job_exe_id = job_exe.id
        job_exe_output.job = job_exe.job
        job_exe_output.job_type = job_exe.job_type
        job_exe_output.exe_num = job_exe.exe_num
        if not output:
            output = JobResults()
        job_exe_output.output = output.get_dict()
        job_exe_output.save()

    return job_exe

def create_seed_manifest(name=None, jobVersion=None, packageVersion=None, title=None,
                         description=None, tags=None, maintainer=None, timeout=None,
                         command=None, inputs_files=None, inputs_json=None,
                         outputs_files=None, outputs_json=None, mounts=None, settings=None,
                         resources=None, errors=None):
    manifest = copy.deepcopy(COMPLETE_MANIFEST)

    if not name:
        global JOB_TYPE_NAME_COUNTER
        name = 'test-job-type-%i' % JOB_TYPE_NAME_COUNTER
        JOB_TYPE_NAME_COUNTER += 1
    manifest['job']['name'] = name

    if jobVersion:
        manifest['job']['jobVersion'] = jobVersion
    if packageVersion:
        manifest['job']['packageVersion'] = packageVersion
    if title:
        manifest['job']['title'] = title
    if description:
        manifest['job']['description'] = description
    if tags:
        manifest['job']['tags'] = tags
    if maintainer:
        manifest['job']['maintainer'] = maintainer
    if timeout:
        manifest['job']['timeout'] = timeout

    # interface
    if command:
        manifest['job']['interface']['command'] = command
    if inputs_files is not None:
        manifest['job']['interface']['inputs']['files'] = inputs_files
    if inputs_json is not None:
        manifest['job']['interface']['inputs']['json'] = inputs_json
    if outputs_files is not None:
        manifest['job']['interface']['outputs']['files'] = outputs_files
    if outputs_json is not None:
        manifest['job']['interface']['outputs']['json'] = outputs_json

    if mounts is not None:
        manifest['job']['interface']['mounts'] = mounts
    if settings is not None:
        manifest['job']['interface']['settings'] = settings

    # resources
    if resources is not None:
        manifest['job']['resources'] = resources

    if errors is not None:
        manifest['job']['errors'] = errors

    return manifest

def create_seed_job_type(manifest=None, priority=50, max_tries=3, max_scheduled=None, is_active=True,
                         configuration=None, docker_image='fake', is_system=False, job_version='0.1.0',
                         interface=None, interface_command=None, interface_inputs=None, interface_outputs=None,
                         interface_mounts=None, interface_settings=None):
    if not manifest:
        global JOB_TYPE_NAME_COUNTER
        name = 'test-job-type-%i' % JOB_TYPE_NAME_COUNTER
        JOB_TYPE_NAME_COUNTER += 1

        if not interface:
            interface = {
                'command': '${INPUT_IMAGE} ${OUTPUT_DIR}',
                'inputs': {
                    'files': [{'name': 'INPUT_IMAGE', 'mediaTypes': ['image/png'], 'required': True}]
                },
                'outputs': {
                    'files': [{'name': 'OUTPUT_IMAGE', 'pattern': '*_watermark.png', 'mediaType': 'image/png'}]
                },
                'mounts': [
                  {
                    'name': 'MOUNT_PATH',
                    'path': '/the/container/path',
                    'mode': 'ro'
                  }
                ],
                'settings': [
                  {
                    'name': 'VERSION',
                    'secret': False
                  },
                  {
                    'name': 'DB_HOST',
                    'secret': False
                  },
                  {
                    'name': 'DB_PASS',
                   'secret': True
                  }
                ]
            }

        if interface_command:
            interface['command'] = interface_command
        if interface_inputs:
            interface['inputs'] = interface_inputs
        if interface_outputs:
            interface['outputs'] = interface_outputs
        if interface_mounts:
            interface['mounts'] = interface_mounts
        if interface_settings:
            interface['settings'] = interface_settings

        manifest = {
            'seedVersion': '1.0.0',
            'job': {
                'name': name,
                'jobVersion': job_version,
                'packageVersion': '0.1.0',
                'title': 'Image Watermarker',
                'description': 'Processes an input PNG and outputs watermarked PNG.',
                'maintainer': {
                    'name': 'John Doe',
                    'email': 'jdoe@example.com'
                },
                'timeout': 30,
                'interface': interface,
                'resources': {
                    'scalar': [
                        {'name': 'cpus', 'value': 1.0},
                        {'name': 'mem', 'value': 64.0}
                    ]
                },
                'errors': [
                    {
                        'code': 1,
                        'name': 'image-corrupt',
                        'title': 'Image Corrupt',
                        'description': 'Image input is not recognized as a valid PNG.',
                        'category': 'data'
                    }
                ]
            }
        }

    if not configuration:
        configuration = {
            'version': '6',
            'priority': priority,
            'output_workspaces': {'default': storage_test_utils.create_workspace().name}
        }
        configuration = JobConfigurationV6(config=configuration).get_dict()

    job_type = JobType.objects.create(name=manifest['job']['name'], version=manifest['job']['jobVersion'],
                                      manifest=manifest, max_tries=max_tries, max_scheduled=max_scheduled,
                                      is_active=is_active, configuration=configuration, docker_image=docker_image,
                                      is_system=is_system)



    version_array = job_type.get_job_version_array(manifest['job']['jobVersion'])
    job_type.version_array = version_array
    job_type.save()
    JobTypeRevision.objects.create_job_type_revision(job_type)
    return job_type

def edit_job_type_v6(job_type, manifest_dict=None, docker_image=None, icon_code=None, is_active=None,
                     is_published=None, is_paused=None, max_scheduled=None, configuration_dict=None):
    """Updates a job type, including creating a new revision for unit testing
    """

    manifest = SeedManifest(manifest_dict, do_validate=True)

    configuration = None
    if configuration_dict:
        configuration = JobConfigurationV6(configuration_dict, do_validate=True).get_configuration()

    JobType.objects.edit_job_type_v6(job_type.id, manifest=manifest, docker_image=docker_image,
                         icon_code=icon_code, is_active=is_active, is_paused=is_paused,
                         is_published=is_published, max_scheduled=max_scheduled, configuration=configuration)

def create_running_job_exe(agent_id='agent_1', job_type=None, job=None, node=None, timeout=None, input_file_size=10.0,
                           queued=None, started=None, resources=None, priority=None, num_exes=1):
    """Creates a running job execution for unit testing

    :returns: The running job execution
    :rtype: :class:`job.execution.job_exe.RunningJobExecution`
    """

    when = timezone.now()
    if not job:
        job = create_job(job_type=job_type, status='RUNNING', input_file_size=input_file_size, num_exes=num_exes)
    job_type = job.job_type

    # Configuration that occurs at queue time
    input_files = {}
    input_file_ids = job.get_job_data().get_input_file_ids()
    if input_file_ids:
        for input_file in ScaleFile.objects.get_files_for_queued_jobs(input_file_ids):
            input_files[input_file.id] = input_file
    exe_config = QueuedExecutionConfigurator(input_files).configure_queued_job(job)

    job_exe = JobExecution()
    job_exe.set_cluster_id('1234', job.id, job.num_exes)
    job_exe.job = job
    job_exe.job_type = job_type
    job_exe.exe_num = job.num_exes
    if not node:
        node = node_utils.create_node()
    job_exe.node = node
    if not timeout:
        timeout = job.get_job_interface().get_timeout()
    job_exe.timeout = timeout
    job_exe.input_file_size = input_file_size
    if not resources:
        resources = job.get_resources()
    job_exe.resources = resources.get_json().get_dict()
    job_exe.configuration = exe_config.get_dict()
    if not queued:
        queued = when
    job_exe.queued = queued
    if not started:
        started = when + datetime.timedelta(seconds=1)
    job_exe.started = started
    job_exe.save()

    if not priority:
        priority = job.priority

    # Configuration that occurs at schedule time
    workspaces = {}
    for workspace in Workspace.objects.all():
        workspaces[workspace.name] = workspace
    secret_config = ScheduledExecutionConfigurator(workspaces).configure_scheduled_job(job_exe, job_type,
                                                                                       job_type.get_job_interface(),'INFO')
    return RunningJobExecution(agent_id, job_exe, job_type, secret_config, priority)


def create_task_status_update(task_id, agent_id, status, when, exit_code=None, reason=None, source=None, message=None,
                              data=None):
    """Creates a job model for unit testing

    :param task_id: The unique ID of the task
    :type task_id: string
    :param agent_id: The agent ID for the task
    :type agent_id: string
    :param status: The status of the task
    :type status: string
    :param when: The timestamp of the update
    :type when: :class:`datetime.datetime`
    :param exit_code: The task's exit code
    :type exit_code: int
    :param reason: The reason
    :type reason: string
    :param source: The source
    :type source: string
    :param message: The message
    :type message: string
    :param data: The data dict
    :type data: dict
    :returns: The task status update
    :rtype: :class:`job.tasks.update.TaskStatusUpdate`
    """

    if data is None:
        data = {}

    task_update_model = TaskUpdate()
    task_update_model.task_id = task_id
    task_update_model.timestamp = when
    task_update_model.message = message
    task_update_model.source = source
    task_update_model.reason = reason
    update = TaskStatusUpdate(task_update_model, agent_id, data)
    update.status = status
    if exit_code is not None:
        update.exit_code = exit_code
    return update

def create_input_file(job=None, input_file=None, job_input=None, file_name='my_test_file.txt', media_type='text/plain',
                      file_size=100, file_path=None, workspace=None, countries=None, is_deleted=False, data_type_tags=[],
                      last_modified=None, source_started=None, source_ended=None):
    """Creates a Scale file and job input file model for unit testing

    :returns: The file model
    :rtype: :class:`storage.models.ScaleFile`
    """

    if not job:
        job = create_job()
    if not job_input:
        job_input = 'test_input'
    if not input_file:
        input_file = storage_test_utils.create_file(file_name=file_name, media_type=media_type, file_size=file_size,
                                                    file_path=file_path, workspace=workspace, countries=countries,
                                                    is_deleted=is_deleted, data_type_tags=data_type_tags,
                                                    last_modified=last_modified, source_started=source_started,
                                                    source_ended=source_ended)

    JobInputFile.objects.create(job=job, input_file=input_file, job_input=job_input)

    return input_file
