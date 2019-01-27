"""Defines the class that handles ingest trigger rules"""
from __future__ import unicode_literals

import logging

from django.db import transaction

from ingest.triggers.configuration.ingest_trigger_rule import IngestTriggerRuleConfiguration
from ingest.handlers.recipe_handler import RecipeHandler
from ingest.handlers.recipe_rule import RecipeRule
from ingest.models import IngestEvent
from job.configuration.data.job_data import JobData
from job.models import JobType
from queue.models import Queue
from recipe.seed.recipe_data import RecipeData
from recipe.configuration.data.recipe_data import LegacyRecipeData
from recipe.models import RecipeType
from storage.models import Workspace
from trigger.handler import TriggerRuleHandler
from trigger.models import TriggerEvent

logger = logging.getLogger(__name__)

INGEST_TYPE = 'INGEST'
RECIPE_TYPE = 'RECIPE'


class IngestTriggerHandler(TriggerRuleHandler):
    """Handles ingest trigger rules
    """

    def __init__(self):
        """Constructor
        """

        super(IngestTriggerHandler, self).__init__(INGEST_TYPE)

    def create_configuration(self, config_dict):
        """See :meth:`trigger.handler.TriggerRuleHandler.create_configuration`
        """

        return IngestTriggerRuleConfiguration(INGEST_TYPE, config_dict)

    @transaction.atomic
    def process_ingested_source_file(self, source_file, when):
        """Processes the given ingested source file by checking it against all ingest trigger rules and creating the
        corresponding jobs and recipes for any triggered rules. All database changes are made in an atomic transaction.

        :param source_file: The source file that was ingested
        :type source_file: :class:`source.models.SourceFile`
        :param when: When the source file was ingested
        :type when: :class:`datetime.datetime`
        """

        msg = 'Processing trigger rules for ingested source file with media type %s and data types %s'
        logger.info(msg, source_file.media_type, str(list(source_file.get_data_type_tags())))

        any_rules = False
        for entry in RecipeType.objects.get_active_trigger_rules(INGEST_TYPE):
            rule = entry[0]
            thing_to_create = entry[1]
            rule_config = rule.get_configuration()
            condition = rule_config.get_condition()

            if condition.is_condition_met(source_file):
                logger.info(condition.get_triggered_message())
                any_rules = True

                event = self._create_ingest_trigger_event(source_file, rule, when)
                workspace = Workspace.objects.get(name=rule_config.get_workspace_name())

                if isinstance(thing_to_create, JobType):
                    job_type = thing_to_create
                    job_data = JobData({})
                    job_data.add_file_input(rule_config.get_input_data_name(), source_file.id)
                    job_type.get_job_interface().add_workspace_to_data(job_data, workspace.id)
                    logger.info('Queuing new job of type %s %s', job_type.name, job_type.version)
                    Queue.objects.queue_new_job(job_type, job_data, event)
                elif isinstance(thing_to_create, RecipeType):
                    recipe_type = thing_to_create
                    recipe_data = LegacyRecipeData({})
                    recipe_data.add_file_input(rule_config.get_input_data_name(), source_file.id)
                    recipe_data.set_workspace_id(workspace.id)
                    logger.info('Queuing new recipe of type %s %s', recipe_type.name, recipe_type.version)
                    Queue.objects.queue_new_recipe(recipe_type, recipe_data, event)

        if not any_rules:
            logger.info('No rules triggered')

    @transaction.atomic
    def kick_off_recipe_from_ingest(self, strike, source_file, source_recipe_config, when):
        """Processes the given ingested source file by kicking off its recipe.
        All database changes are made in an atomic transaction.

        :param strike: The strike that triggered the ingest
        :type strike: :class:`ingest.models.Strike`
        :param source_file: The source file that was ingested
        :type source_file: :class:`source.models.SourceFile`
        :param soruce_recipe_config:
        :type: source_recipe_config: dict
        :param when: When the source file was ingested
        :type when: :class:`datetime.datetime`
        """

        # Create the recipe handler associated with the ingest strike/scan
        recipe_name = source_recipe_config['name']
        handler = RecipeHandler(source_recipe_config['name'])
        for condition in source_recipe_config['conditions']:
            media_types = condition['media_types'] if 'media_types' in condition else None
            data_types = condition['data_types'] if 'data_types' in condition else None
            # media_types = condition['any_data_types'] if 'media_types' in condition else None
            not_data_types = condition['not_data_types'] if 'not_data_types' in condition else None
            handler.add_rule(RecipeRule(condition['input_name'], media_types, data_types, not_data_types))

        # MATCH INPUT TO INPUT NAME
        input_rule = handler.rule_matches(source_file)
        if not input_rule:
            raise Exception('No recipe input data matching source file')

        recipe_data = RecipeData({})
        recipe_data.add_file_input(input_rule.input_name, source_file.id)

        # need to do?
        event = self._create_ingest_event(strike, source_file, None, when)
        # recipe_config = None
        # logger.info('Queuing new recipe of type %s %s', recipe_type.name, recipe_type.version)
        # recipe_type =

        import pdb; pdb.set_trace()
        Queue.objects.queue_new_recipe_ingest_v6(RecipeType.objects.get(name=recipe_name), recipe_data._new_data, event)

    def _create_ingest_trigger_event(self, source_file, trigger_rule, when):
        """Creates in the database and returns a trigger event model for the given ingested source file and trigger rule

        :param source_file: The source file that was ingested
        :type source_file: :class:`source.models.SourceFile`
        :param trigger_rule: The rule that triggered the event
        :type trigger_rule: :class:`trigger.models.TriggerRule`
        :param when: When the source file was ingested
        :type when: :class:`datetime.datetime`
        :returns: The new trigger event
        :rtype: :class:`trigger.models.TriggerEvent`

        :raises trigger.configuration.exceptions.InvalidTriggerRule: If the configuration is invalid
        """

        description = {'version': '1.0', 'file_id': source_file.id, 'file_name': source_file.file_name}
        return TriggerEvent.objects.create_trigger_event(INGEST_TYPE, trigger_rule, description, when)

    def _create_ingest_event(self, strike, source_file, rule, when):
        """Creates in the database and returns a trigger event model for the given ingested source file and recipe type

        :param strike: The strike that triggered the ingest
        :type strike: :class:`ingest.models.Strike`
        :param source_file: The source file that was ingested
        :type source_file: :class:`source.models.SourceFile`
        :param rule: The rule that triggered the event
        :type rule: :class:`trigger.models.TriggerRule`
        :param when: When the source file was ingested
        :type when: :class:`datetime.datetime`
        :returns: The new trigger event
        :rtype: :class:`trigger.models.TriggerEvent`
        """

        description = {'version': '1.0', 'file_id': source_file.id, 'file_name': source_file.file_name}
        return IngestEvent.objects.create_strike_ingest_event(strike, description, when)