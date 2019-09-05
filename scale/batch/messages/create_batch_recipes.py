"""Defines a command message that creates batch recipes"""
from __future__ import unicode_literals

import logging

from django.utils.timezone import now

from batch.models import Batch
from data.data.data import Data
from data.data.value import FileValue
from data.data.json.data_v6 import convert_data_to_v6_json
from data.interface.exceptions import InvalidInterfaceConnection
from data.models import DataSet, DataSetFile
from messaging.messages.message import CommandMessage
from recipe.messages.create_recipes import create_reprocess_messages, create_batch_recipes_messages
from recipe.models import Recipe, RecipeTypeRevision, RecipeInputFile
from storage.models import ScaleFile

# How many recipes to handle in a single execution of this message
MAX_RECIPE_NUM = 1000


logger = logging.getLogger(__name__)


def create_batch_recipes_message(batch_id):
    """Creates a message to create the recipes for the given batch

    :param batch_id: The batch ID
    :type batch_id: int
    :return: The message
    :rtype: :class:`batch.messages.create_batch_recipes.CreateBatchRecipes`
    """

    message = CreateBatchRecipes()
    message.batch_id = batch_id

    return message


class CreateBatchRecipes(CommandMessage):
    """Command message that creates batch recipes
    """

    def __init__(self):
        """Constructor
        """

        super(CreateBatchRecipes, self).__init__('create_batch_recipes')

        self.batch_id = None
        self.is_prev_batch_done = False  # Indicates if all recipes from previous batch have been handled
        self.current_recipe_id = None  # Keeps track of the last recipe that was reprocessed
        self.current_dataset_file_id = None # Keeps track of the last dataset file that was processed

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        json_dict = {'batch_id': self.batch_id, 'is_prev_batch_done': self.is_prev_batch_done}
        if self.current_recipe_id is not None:
            json_dict['current_recipe_id'] = self.current_recipe_id
        if self.current_dataset_file_id is not None:
            json_dict['current_dataset_file_id'] = self.current_dataset_file_id

        return json_dict

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = CreateBatchRecipes()
        message.batch_id = json_dict['batch_id']
        message.is_prev_batch_done = json_dict['is_prev_batch_done']
        if 'current_recipe_id' in json_dict:
            message.current_recipe_id = json_dict['current_recipe_id']
        if 'current_dataset_file_id' in json_dict:
            message.current_dataset_file_id = json_dict['current_dataset_file_id']

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """
        batch = Batch.objects.select_related('recipe_type', 'recipe_type_rev').get(id=self.batch_id)
        definition = batch.get_definition()
        new_messages = []
        
        # Reprocess recipes from previous batch or create a new batch
        if not self.is_prev_batch_done:
            if batch.superseded_batch_id:
                new_messages.extend(self._handle_previous_batch(batch, definition))
            else:
                new_messages.extend(self._handle_new_batch(batch, definition))

        if self.is_prev_batch_done:
            if batch.superseded_batch_id:
                logger.info('All re-processing messages created, marking recipe creation as done')
            else:
                logger.info('All new recipe messages created, marking recipe creation as done')
            Batch.objects.mark_creation_done(self.batch_id, now())
        else:
            logger.info('Creating new message for next set of batch recipes')
            msg = CreateBatchRecipes.from_json(self.to_json())
            self.new_messages.append(msg)

        self.new_messages.extend(new_messages)
        return True
        
    def _handle_new_batch(self, batch, definition):
        """Handles creating a new batch of recipes with the defined dataset, returning any messages needed for the batch
        
        :param batch: The batch
        :type batch: :class:`batch.models.Batch`
        :param definition: The batch definition
        :type definition: :class:`batch.definition.definition.BatchDefinition`
        :return: The messages needed for the re-processing
        :rtype: list
        """
        
        messages = []
        dataset = DataSet.objects.get(pk=definition.dataset)
        dataset_definition = dataset.get_definition()
        recipe_type_rev = RecipeTypeRevision.objects.get_revision(name=batch.recipe_type.name, revision_num=batch.recipe_type_rev.revision_num)
        recipe_inputs = recipe_type_rev.get_definition().get_input_keys()
        
        # combine the parameters
        dataset_parameters = dataset_definition.global_parameters
        for param in dataset_definition.parameters.parameters:
            dataset_parameters.add_parameter(dataset_definition.parameters.parameters[param])

        try:
            recipe_type_rev.get_definition().input_interface.validate_connection(dataset_parameters)
        except InvalidInterfaceConnection as ex:
            # No recipe inputs match the dataset 
            logger.info('None of the dataset parameters matched the recipe type inputs; No recipes will be created')
            self.is_prev_batch_done = True
            return messages

        # Get previous recipes for dataset files:
        ds_files = DataSetFile.objects.get_dataset_files(dataset.id).values_list('scale_file_id', flat=True)
        recipe_ids = RecipeInputFile.objects.filter(input_file_id__in=ds_files).values_list('recipe_id', flat=True)
        recipe_file_ids = RecipeInputFile.objects.filter(input_file_id__in=ds_files,
                                                         recipe__recipe_type=batch.recipe_type, 
                                                         recipe__recipe_type_rev=batch.recipe_type_rev).values_list('input_file_id', flat=True)
        extra_files_qry = ScaleFile.objects.filter(id__in=ds_files)
        
        recipe_count = 0
        # Reprocess previous recipes
        if definition.supersedes:
            if len(recipe_ids) > 0:
                # Create re-process messages for all recipes
                recipe_qry = Recipe.objects.filter(id__in=recipe_ids).order_by('-id')
                if self.current_recipe_id:
                    recipe_qry = recipe_qry.filter(id__lt=self.current_recipe_id)
                
                root_recipe_ids = []
                for recipe in recipe_qry.defer('input')[:MAX_RECIPE_NUM]:
                    root_recipe_ids.append(recipe.id)
                    self.current_recipe_id = recipe.id
                recipe_count = len(root_recipe_ids)
        
                if recipe_count > 0:
                    logger.info('Found %d recipe(s) from previous batch to reprocess, creating messages', recipe_count)
                    msgs = create_reprocess_messages(root_recipe_ids, batch.recipe_type.name,
                                                     batch.recipe_type_rev.revision_num, batch.event_id, batch_id=batch.id,
                                                     forced_nodes=definition.forced_nodes)
                    messages.extend(msgs)

            # Filter down the extra files to exclude those we've already re-processed
            extra_files_qry = extra_files_qry.exclude(id__in=recipe_file_ids)

        # If we have data that didn't match any previous recipes
        if self.current_dataset_file_id:
            extra_files_qry = extra_files_qry.filter(id__lt=self.current_dataset_file_id)
        extra_file_ids = list(extra_files_qry.order_by('-id').values_list('id', flat=True)[:(MAX_RECIPE_NUM-recipe_count)])

        if extra_file_ids:
            self.current_dataset_file_id = extra_file_ids[-1]

        if len(extra_file_ids) > 0:
            logger.info('Found %d files that do not have previous recipes to re-process', len(extra_file_ids))
            
            input_data = []
            for file in DataSetFile.objects.get_dataset_files(dataset.id).filter(scale_file__id__in=extra_file_ids):
                data = Data()
                data.add_value(FileValue(file.parameter_name, [file.scale_file_id]))
                input_data.append(convert_data_to_v6_json(data).get_dict())
                
            msgs = create_batch_recipes_messages(batch.recipe_type.name, batch.recipe_type.revision_num, input_data, batch.event_id, batch_id=batch.id)
            messages.extend(msgs)
            recipe_count += len(input_data)

        if recipe_count < MAX_RECIPE_NUM:
            # Handled less than the max number of recipes, so recipes from previous batch must be done
            self.is_prev_batch_done = True
        
        return messages

    def _handle_previous_batch(self, batch, definition):
        """Handles re-processing all recipes in the previous batch, returning any messages needed for the re-processing

        :param batch: The batch
        :type batch: :class:`batch.models.Batch`
        :param definition: The batch definition
        :type definition: :class:`batch.definition.definition.BatchDefinition`
        :return: The messages needed for the re-processing
        :rtype: list
        """

        messages = []
        if batch.superseded_batch_id and definition.root_batch_id is None:
            self.is_prev_batch_done = True
            return messages

        # Re-processing a previous batch
        recipe_qry = Recipe.objects.filter(batch_id=batch.superseded_batch_id, recipe__isnull=True)
        
        # Only handle MAX_RECIPE_NUM at a time
        if self.current_recipe_id:
            recipe_qry = recipe_qry.filter(id__lt=self.current_recipe_id)
        recipe_qry = recipe_qry.order_by('-id')

        root_recipe_ids = []
        last_recipe_id = None
        for recipe in recipe_qry.defer('input')[:MAX_RECIPE_NUM]:
            last_recipe_id = recipe.id
            if recipe.root_superseded_recipe_id is not None:
                root_recipe_ids.append(recipe.root_superseded_recipe_id)
            else:
                root_recipe_ids.append(recipe.id)
        recipe_count = len(root_recipe_ids)

        self.current_recipe_id = last_recipe_id
        if recipe_count > 0:
            logger.info('Found %d recipe(s) from previous batch to reprocess, creating messages', recipe_count)
            msgs = create_reprocess_messages(root_recipe_ids, batch.recipe_type.name,
                                             batch.recipe_type_rev.revision_num, batch.event_id, batch_id=batch.id,
                                             forced_nodes=definition.forced_nodes)
            messages.extend(msgs)

        if recipe_count < MAX_RECIPE_NUM:
            # Handled less than the max number of recipes, so recipes from previous batch must be done
            self.is_prev_batch_done = True

        return messages
