"""Defines the class that handles ingest trigger rules"""
from __future__ import unicode_literals

import logging

from django.db import transaction

from data.data.data import Data
from data.data.json.data_v6 import convert_data_to_v6_json
from data.data.value import FileValue
from ingest.models import IngestEvent, Scan, Strike
from messaging.manager import CommandMessageManager
from recipe.messages.create_recipes import create_recipes_messages
from recipe.models import RecipeType, RecipeTypeRevision
from trigger.models import TriggerEvent

logger = logging.getLogger(__name__)

RECIPE_TYPE = 'RECIPE'


class IngestRecipeHandler(object):
    """Handles ingest trigger rules
    """

    def __init__(self):
        """Constructor
        """

        super(IngestRecipeHandler, self).__init__()

    def process_manual_ingested_source_file(self, ingest_id, source_file, when, recipe_type_id):
        """Processes a manual ingest where a strike or scan is not involved. All database
        changes are made in an atomic transaction

        :param ingest_id:
        :type ingest_id: int

        :param source_file: The source file that was ingested
        :type source_file: :class:`source.models.SourceFile`
        :param when: When the source file was ingested
        :type when: :class:`datetime.datetime`
        :param recipe_type_id: id of the Recipe type to kick off
        :type recipe_type_id: int
        """

        recipe_type = RecipeType.objects.get(id=recipe_type_id)

        if recipe_type and recipe_type.is_active:
            recipe_data = Data()
            input_name = recipe_type.get_definition().get_input_keys()[0]
            recipe_data.add_value(FileValue(input_name, [source_file.id]))
            event = self._create_trigger_event(None, source_file, when)
            ingest_event = self._create_ingest_event(ingest_id, None, source_file, when)

            logger.info('Queueing new recipe of type %s %s', recipe_type.name, recipe_type.revision_num)
            from queue.models import Queue
            Queue.objects.queue_new_recipe_v6(recipe_type, recipe_data, event, ingest_event)

            # messages = create_recipes_messages(recipe_type.name, recipe_type.revision_num,
            #                                    convert_data_to_v6_json(recipe_data).get_dict(),
            #                                    event.id, ingest_event.id)
            # CommandMessageManager().send_messages(messages)
            
        else:
            logger.info('No recipe type found for id %s or recipe type is inactive' % recipe_type_id)

    def process_ingested_source_file(self, ingest_id, source, source_file, when):
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
        recipe_revision = source_recipe_config['revision_num'] if 'revision_num' in source_recipe_config else None

        recipe_type = RecipeType.objects.get(name=recipe_name)
        if recipe_revision:
            recipe_type = RecipeTypeRevision.objects.get_revision(recipe_name, recipe_revision).recipe_type

        if len(recipe_type.get_definition().get_input_keys()) == 0:
            logger.info('No inputs defined for recipe %s. Recipe will not be run.' % recipe_name)
            return

        if recipe_type and recipe_type.is_active:
            # Assuming one input per recipe, so pull the first defined input you find
            recipe_data = Data()
            input_name = recipe_type.get_definition().get_input_keys()[0]
            recipe_data.add_value(FileValue(input_name, [source_file.id]))
            event = self._create_trigger_event(source, source_file, when)
            ingest_event = self._create_ingest_event(ingest_id, source, source_file, when)

            logger.info('Queueing new recipe of type %s %s', recipe_type.name, recipe_type.revision_num)
            from queue.models import Queue
            Queue.objects.queue_new_recipe_v6(recipe_type, recipe_data, event, ingest_event)

            # This can cause a race condition with a slow DB.
            # messages = create_recipes_messages(recipe_type.name, recipe_type.revision_num,
            #                                    convert_data_to_v6_json(recipe_data).get_dict(),
            #                                    event.id, ingest_event.id)
            # CommandMessageManager().send_messages(messages)

        else:
            logger.info('No recipe type found for %s %s or recipe type is inactive' % (recipe_name, recipe_revision))

    def process_ingested_source_file_cm(self, ingest_id, source, source_file, when):
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
        recipe_revision = source_recipe_config['revision_num'] if 'revision_num' in source_recipe_config else None

        recipe_type = RecipeType.objects.get(name=recipe_name)
        if recipe_revision:
            recipe_type = RecipeTypeRevision.objects.get_revision(recipe_name, recipe_revision).recipe_type
            
        if len(recipe_type.get_definition().get_input_keys()) == 0:
            logger.info('No inputs defined for recipe %s. Recipe will not be run.' % recipe_name)
            return

        if recipe_type and recipe_type.is_active:
            # Assuming one input per recipe, so pull the first defined input you find
            recipe_data = Data()
            input_name = recipe_type.get_definition().get_input_keys()[0]
            recipe_data.add_value(FileValue(input_name, [source_file.id]))
            event = self._create_trigger_event(source, source_file, when)
            ingest_event = self._create_ingest_event(ingest_id, source, source_file, when)

            # This can cause a race condition with a slow DB.
            messages = create_recipes_messages(recipe_type.name, recipe_type.revision_num,
                                               convert_data_to_v6_json(recipe_data).get_dict(), 
                                               event.id, ingest_event.id)
            CommandMessageManager().send_messages(messages)
            
        else:
            logger.info('No recipe type found for %s %s or recipe type is inactive' % (recipe_name, recipe_revision))

    def _create_ingest_event(self, ingest_id, source, source_file, when):
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

        event = None
        description = {'version': '1.0', 'file_id': source_file.id, 'file_name': source_file.file_name}
        with transaction.atomic():
            if type(source) is Strike:
                event = IngestEvent.objects.create_strike_ingest_event(ingest_id, source, description, when)
            elif type(source) is Scan:
                event = IngestEvent.objects.create_scan_ingest_event(ingest_id, source, description, when)
            elif ingest_id:
                event = IngestEvent.objects.create_manual_ingest_event(ingest_id, description, when)
            else:
                logger.info('No valid source event for source file %s', source_file.file_name)
        return event

    def _create_trigger_event(self, source, source_file, when):
        """Creates in the database and returns a trigger event model for the given ingested source file and recipe type

        :param source: The source of the ingest
        :param source_file: The source file that was ingested
        :type source_file: :class:`source.models.SourceFile`
        :param when: When the source file was ingested
        :type when: :class:`datetime.datetime`
        :returns: The new trigger event
        :rtype: :class:`trigger.models.TriggerEvent`

        :raises trigger: If the trigger is invalid
        """

        description = {'version': '1.0', 'file_id': source_file.id, 'file_name': source_file.file_name}
        event_type = ''
        
        if type(source) is Strike:
            event_type = 'STRIKE_INGEST'
        elif type(source) is Scan:
            event_type = 'SCAN_INGEST'
        else:
            event_type = 'MANUAL_INGEST'
        
        with transaction.atomic():
            event = TriggerEvent.objects.create_trigger_event(event_type, None, description, when)
        return event
