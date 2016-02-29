'''Defines the class that handles parse trigger rules'''
from __future__ import unicode_literals

import logging

from django.db import transaction

from job.configuration.data.job_data import JobData
from job.models import JobType
from queue.models import Queue
from recipe.configuration.data.recipe_data import RecipeData
from recipe.models import RecipeType
from source.triggers.configuration.parse_trigger_rule import ParseTriggerRuleConfiguration
from storage.models import Workspace
from trigger.handler import TriggerRuleHandler
from trigger.models import TriggerEvent


logger = logging.getLogger(__name__)


PARSE_TYPE = 'PARSE'


class ParseTriggerHandler(TriggerRuleHandler):
    '''Handles parse trigger rules
    '''

    def __init__(self):
        '''Constructor
        '''

        super(ParseTriggerHandler, self).__init__(PARSE_TYPE)

    def create_configuration(self, config_dict):
        '''See :meth:`trigger.handler.TriggerRuleHandler.create_configuration`
        '''

        return ParseTriggerRuleConfiguration(PARSE_TYPE, config_dict)

    @transaction.atomic
    def process_parsed_source_file(self, source_file):
        '''Processes the given parsed source file by checking it against all parse trigger rules and creating the
        corresponding jobs and recipes for any triggered rules. All database changes are made in an atomic transaction.

        :param source_file: The source file that was parsed
        :type source_file: :class:`source.models.SourceFile`
        '''

        msg = 'Processing trigger rules for parsed source file with media type %s and data types %s'
        logger.info(msg, source_file.media_type, str(list(source_file.get_data_type_tags())))

        any_rules = False
        for entry in RecipeType.objects.get_active_trigger_rules(PARSE_TYPE):
            rule = entry[0]
            thing_to_create = entry[1]
            rule_config = rule.get_configuration()
            condition = rule_config.get_condition()

            if condition.is_condition_met(source_file):
                logger.info(condition.get_triggered_message())
                any_rules = True

                event = self._create_parse_trigger_event(source_file, rule)
                workspace = Workspace.objects.get(name=rule_config.get_workspace_name())

                if isinstance(thing_to_create, JobType):
                    job_type = thing_to_create
                    job_data = JobData({})
                    job_data.add_file_input(rule_config.get_input_data_name(), source_file.id)
                    job_type.get_job_interface().add_workspace_to_data(job_data, workspace.id)
                    logger.info('Queuing new job of type %s %s', job_type.name, job_type.version)
                    Queue.objects.queue_new_job(job_type, job_data.get_dict(), event)
                elif isinstance(thing_to_create, RecipeType):
                    recipe_type = thing_to_create
                    recipe_data = RecipeData({})
                    recipe_data.add_file_input(rule_config.get_input_data_name(), source_file.id)
                    recipe_data.set_workspace_id(workspace.id)
                    logger.info('Queuing new recipe of type %s %s', recipe_type.name, recipe_type.version)
                    Queue.objects.queue_new_recipe(recipe_type, recipe_data.get_dict(), event)

        if not any_rules:
            logger.info('No rules triggered')

    def _create_parse_trigger_event(self, source_file, trigger_rule):
        '''Creates in the database and returns a trigger event model for the given parsed source file and trigger rule

        :param source_file: The source file that was parsed
        :type source_file: :class:`source.models.SourceFile`
        :param trigger_rule: The rule that triggered the event
        :type trigger_rule: :class:`trigger.models.TriggerRule`
        :returns: The new trigger event
        :rtype: :class:`trigger.models.TriggerEvent`

        :raises trigger.configuration.exceptions.InvalidTriggerRule: If the configuration is invalid
        '''

        description = {'version': '1.0', 'file_id': source_file.id, 'file_name': source_file.file_name}
        return TriggerEvent.objects.create_trigger_event(PARSE_TYPE, trigger_rule, description, source_file.parsed)
