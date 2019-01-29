"""Defines the class that handles ingest trigger rules"""
from __future__ import unicode_literals

import logging

from django.db import transaction

from ingest.triggers.configuration.ingest_trigger_rule import IngestTriggerRuleConfiguration
from ingest.handlers.recipe_handler import RecipeHandler
from ingest.handlers.recipe_rule import RecipeRule
from ingest.models import IngestEvent, Scan, Strike
from job.configuration.data.job_data import JobData
from job.models import JobType
from queue.models import Queue
from recipe.seed.recipe_data import RecipeData
from recipe.configuration.data.recipe_data import LegacyRecipeData
from recipe.models import RecipeType
from storage.models import Workspace
from trigger.handler import TriggerRuleHandler

logger = logging.getLogger(__name__)

RECIPE_TYPE = 'RECIPE'

class IngestRecipeHandler(object):
    """Handles ingest trigger rules
    """

    def __init__(self):
        """Constructor
        """

        super(IngestRecipeHandler, self).__init__()#RECIPE_TYPE)

    # def create_configuration(self, config_dict):
    #     """See :meth:`trigger.handler.TriggerRuleHandler.create_configuration`
    #     """

    #     return IngestTriggerRuleConfiguration(RECIPE_TYPE, config_dict)

    @transaction.atomic
    def process_ingested_source_file(self, source, source_file, when):
        """Processes the given ingested source file by kicking off its recipe.
        All database changes are made in an atomic transaction.

        :param source: The strike that triggered the ingest
        :type scan: `object`

        :param source_file: The source file that was ingested
        :type source_file: :class:`source.models.SourceFile`
        :param when: When the source file was ingested
        :type when: :class:`datetime.datetime`
        """
        # Create the recipe handler associated with the ingest strike/scan
        source_recipe_config = source.configuration['recipe']
        recipe_name = source_recipe_config['name']
        handler = RecipeHandler(source_recipe_config['name'])
        for condition in source_recipe_config['conditions']:
            media_types = condition['media_types'] if 'media_types' in condition else None
            data_types = condition['data_types'] if 'data_types' in condition else None
            any_data_types = condition['any_data_types'] if 'any_data_types' in condition else None
            not_data_types = condition['not_data_types'] if 'not_data_types' in condition else None
            handler.add_rule(RecipeRule(condition['input_name'], media_types, data_types, any_data_types, not_data_types))

        # MATCH INPUT TO INPUT NAME
        input_rule = handler.rule_matches(source_file)
        if input_rule:
            recipe_data = RecipeData({})
            recipe_data.add_file_input(input_rule.input_name, source_file.id)

            event = self._create_ingest_event(source, source_file, when)
            recipe_type = RecipeType.objects.get(name=recipe_name)
            logger.info('Queuing new recipe of type %s %s', recipe_type.name, recipe_type.version)
            Queue.objects.queue_new_recipe_ingest_v6(recipe_type, recipe_data._new_data, event)
        else:
            logger.info('No recipe input matches the source file')

    def _create_ingest_event(self, source, source_file, when):
        """Creates in the database and returns a trigger event model for the given ingested source file and recipe type

        :param source: The strike that triggered the ingest
        :type source: :class:`ingest.models.Strike`
        :param source_file: The source file that was ingested
        :type source_file: :class:`source.models.SourceFile`
        :param when: When the source file was ingested
        :type when: :class:`datetime.datetime`
        :returns: The new ingest event
        :rtype: :class:`ingest.models.IngestEvent`
        """

        description = {'version': '1.0', 'file_id': source_file.id, 'file_name': source_file.file_name}
        if type(source) is Strike:
            return IngestEvent.objects.create_strike_ingest_event(source, description, when)
        elif type(source) is Scan:
            return IngestEvent.objects.create_scan_ingest_event(source, description, when)
        else:
            logger.info('No valid source event for source file %s', source_file.file_name)