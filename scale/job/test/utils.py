'''Defines utility methods for testing jobs and job types'''
from __future__ import unicode_literals

import django.utils.timezone as timezone
import trigger.test.utils as trigger_test_utils
from job.configuration.data.exceptions import InvalidConnection
from job.models import Job, JobExecution, JobType, JobTypeRevision
from job.triggers.configuration.trigger_rule import JobTriggerRuleConfiguration
from node.test import utils as node_utils
from trigger.handler import TriggerRuleHandler, register_trigger_rule_handler


JOB_TYPE_NAME_COUNTER = 1
JOB_TYPE_VERSION_COUNTER = 1
JOB_TYPE_CATEGORY_COUNTER = 1

RULE_EVENT_COUNTER = 1


MOCK_TYPE = 'MOCK_JOB_TRIGGER_RULE_TYPE'
MOCK_ERROR_TYPE = 'MOCK_JOB_TRIGGER_RULE_ERROR_TYPE'


class MockTriggerRuleConfiguration(JobTriggerRuleConfiguration):
    '''Mock trigger rule configuration for testing
    '''

    def __init__(self, trigger_rule_type, configuration):
        super(MockTriggerRuleConfiguration, self).__init__(trigger_rule_type, configuration)

    def validate(self):
        pass

    def validate_trigger_for_job(self, job_interface):
        return []


class MockErrorTriggerRuleConfiguration(JobTriggerRuleConfiguration):
    '''Mock error trigger rule configuration for testing
    '''

    def __init__(self, trigger_rule_type, configuration):
        super(MockErrorTriggerRuleConfiguration, self).__init__(trigger_rule_type, configuration)

    def validate(self):
        pass

    def validate_trigger_for_job(self, job_interface):
        raise InvalidConnection('Error!')


class MockTriggerRuleHandler(TriggerRuleHandler):
    '''Mock trigger rule handler for testing
    '''

    def __init__(self):
        super(MockTriggerRuleHandler, self).__init__(MOCK_TYPE)

    def create_configuration(self, config_dict):
        return MockTriggerRuleConfiguration(MOCK_TYPE, config_dict)


class MockErrorTriggerRuleHandler(TriggerRuleHandler):
    '''Mock error trigger rule handler for testing
    '''

    def __init__(self):
        super(MockErrorTriggerRuleHandler, self).__init__(MOCK_ERROR_TYPE)

    def create_configuration(self, config_dict):
        return MockErrorTriggerRuleConfiguration(MOCK_ERROR_TYPE, config_dict)


register_trigger_rule_handler(MockTriggerRuleHandler())
register_trigger_rule_handler(MockErrorTriggerRuleHandler())


def create_job(job_type=None, event=None, status='PENDING', error=None, data=None, num_exes=0, queued=None,
               started=None, ended=None, last_status_change=None, priority=100, results=None):
    '''Creates a job model for unit testing

    :returns: The job model
    :rtype: :class:`job.models.Job`
    '''

    if not job_type:
        job_type = create_job_type()
    if not event:
        event = trigger_test_utils.create_trigger_event()
    if not last_status_change:
        last_status_change = timezone.now()
    if not data:
        data = {
            'version': '1.0',
            'input_data': [],
            'output_data': [],
        }

    job = Job.objects.create_job(job_type, event)
    job.priority = priority
    job.data = data
    job.status = status
    job.num_exes = num_exes
    job.queued = queued
    job.started = started
    job.ended = ended
    job.last_status_change = last_status_change
    job.error = error
    job.results = results
    job.save()
    return job


def create_job_exe(job_type=None, job=None, status='RUNNING', error=None, command_arguments='test_arg', timeout=None,
                   node=None, created=None, queued=None, started=None, pre_started=None, pre_completed=None,
                   job_started=None, job_completed=None, post_started=None, post_completed=None, ended=None,
                   last_modified=None):
    '''Creates a job execution model for unit testing

    :returns: The job execution model
    :rtype: :class:`job.models.JobExecution`
    '''

    when = timezone.now()
    if not job:
        job = create_job(job_type=job_type)
    if not timeout:
        timeout = job.timeout
    if not node:
        node = node_utils.create_node()
    if not created:
        created = when
    if not queued:
        queued = when
    if not started:
        started = when
    if not last_modified:
        last_modified = when

    return JobExecution.objects.create(job=job, status=status, error=error, command_arguments=command_arguments,
                                       timeout=timeout, node=node, created=created, queued=queued, started=started,
                                       pre_started=pre_started, pre_completed=pre_completed, job_started=job_started,
                                       job_completed=job_completed, post_started=post_started,
                                       post_completed=post_completed, ended=ended, last_modified=last_modified)


def create_job_type(name=None, version=None, category=None, interface=None, priority=50, timeout=3600, max_tries=3,
                    max_scheduled=None, cpus=1.0, mem=1.0, disk=1.0, error_mapping=None, is_operational=True, trigger_rule=None):
    '''Creates a job type model for unit testing

    :returns: The job type model
    :rtype: :class:`job.models.JobType`
    '''

    if not name:
        global JOB_TYPE_NAME_COUNTER
        name = 'test-job-type-%i' % JOB_TYPE_NAME_COUNTER
        JOB_TYPE_NAME_COUNTER = JOB_TYPE_NAME_COUNTER + 1

    if not version:
        global JOB_TYPE_VERSION_COUNTER
        version = '%i.0.0' % JOB_TYPE_VERSION_COUNTER
        JOB_TYPE_VERSION_COUNTER = JOB_TYPE_VERSION_COUNTER + 1

    if not category:
        global JOB_TYPE_CATEGORY_COUNTER
        category = 'test-category-%i' % JOB_TYPE_CATEGORY_COUNTER
        JOB_TYPE_CATEGORY_COUNTER = JOB_TYPE_CATEGORY_COUNTER + 1

    if not interface:
        interface = {
            'version': '1.0',
            'command': 'test_cmd',
            'command_arguments': 'test_arg',
            'input_data': [],
            'output_data': [],
            'shared_resources': [],
        }
    if not error_mapping:
        error_mapping = {
            'version': '1.0',
            'exit_codes': {}
        }
    if not trigger_rule:
        trigger_rule = trigger_test_utils.create_trigger_rule()

    job_type = JobType.objects.create(name=name, version=version, category=category, interface=interface,
                                      priority=priority, timeout=timeout, max_tries=max_tries, max_scheduled=max_scheduled,
                                      cpus_required=cpus, mem_required=mem, disk_out_const_required=disk,
                                      error_mapping=error_mapping, is_operational=is_operational, trigger_rule=trigger_rule)
    JobTypeRevision.objects.create_job_type_revision(job_type)
    return job_type


def create_clock_rule(name=None, rule_type='CLOCK', event_type=None, schedule='PT1H0M0S', is_active=True):
    '''Creates a scale clock trigger rule model for unit testing

    :returns: The trigger rule model
    :rtype: :class:`trigger.models.TriggerRule`
    '''

    if not event_type:
        global RULE_EVENT_COUNTER
        event_type = 'TEST_EVENT_%i' % RULE_EVENT_COUNTER
        RULE_EVENT_COUNTER = RULE_EVENT_COUNTER + 1

    config = {
        'version': '1.0',
        'event_type': event_type,
        'schedule': schedule,
    }

    return trigger_test_utils.create_trigger_rule(name=name, trigger_type=rule_type, configuration=config,
                                                  is_active=is_active)


def create_clock_event(rule=None, occurred=None):
    '''Creates a scale clock trigger event model for unit testing

    :returns: The trigger event model
    :rtype: :class:`trigger.models.TriggerEvent`
    '''

    if not rule:
        rule = create_clock_rule()

    if not occurred:
        occurred = timezone.now()

    event_type = None
    if rule.configuration and 'event_type' in rule.configuration:
        event_type = rule.configuration['event_type']

    return trigger_test_utils.create_trigger_event(trigger_type=event_type, rule=rule, occurred=occurred)
