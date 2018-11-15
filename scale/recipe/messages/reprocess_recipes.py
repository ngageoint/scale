"""Defines a command message that reprocesses recipes"""
from __future__ import unicode_literals

import logging

from django.db import transaction
from django.utils.timezone import now

from job.messages.cancel_jobs import create_cancel_jobs_messages
from job.messages.unpublish_jobs import create_unpublish_jobs_messages
from job.models import Job
from messaging.messages.message import CommandMessage
from recipe.handlers.graph_delta import RecipeGraphDelta
from recipe.messages.process_recipe_input import create_process_recipe_input_messages
from recipe.models import Recipe, RecipeNode, RecipeTypeRevision

# This is the maximum number of recipe models that can fit in one message. This maximum ensures that every message of
# this type is less than 25 KiB long and that each message can be processed quickly.
MAX_NUM = 100

MODEL_BATCH_SIZE = 500  # Maximum batch size for creating models


logger = logging.getLogger(__name__)


# TODO: this command message is deprecated and will be removed in v6. Please use the create_recipes command message
# instead
def create_reprocess_recipes_messages(root_recipe_ids, revision_id, event_id, all_jobs=False, job_names=None,
                                      batch_id=None):
    """Creates messages to reprocess the given root recipes

    :param root_recipe_ids: The root recipe IDs
    :type root_recipe_ids: list
    :param revision_id: The ID of the new recipe type revision to use for reprocessing
    :type revision_id: int
    :param event_id: The ID of the event that triggered the reprocessing
    :type event_id: int
    :param all_jobs: Indicates whether all jobs in the recipes should be reprocessed
    :type all_jobs: bool
    :param job_names: Lists jobs that should be reprocessed even if they haven't changed
    :type job_names: list
    :param batch_id: The batch ID if this reprocess belongs to a batch
    :type batch_id: int
    :return: The list of messages
    :rtype: list
    """

    messages = []
    if job_names is None:
        job_names = []

    message = None
    for root_recipe_id in set(root_recipe_ids):  # Ensure no duplicates
        if not message:
            message = ReprocessRecipes()
            message.all_jobs = all_jobs
            message.batch_id = batch_id
            message.event_id = event_id
            message.job_names = job_names
            message.revision_id = revision_id
        elif not message.can_fit_more():
            messages.append(message)
            message = ReprocessRecipes()
            message.all_jobs = all_jobs
            message.batch_id = batch_id
            message.event_id = event_id
            message.job_names = job_names
            message.revision_id = revision_id
        message.add_recipe(root_recipe_id)
    if message:
        messages.append(message)

    return messages


class ReprocessRecipes(CommandMessage):
    """Command message that reprocesses recipes
    """

    def __init__(self):
        """Constructor
        """

        super(ReprocessRecipes, self).__init__('reprocess_recipes')

        self.all_jobs = False
        self.batch_id = None
        self.event_id = None
        self.job_names = []
        self.revision_id = None
        self._root_recipe_ids = []

    def add_recipe(self, root_recipe_id):
        """Adds the given root recipe ID to this message. Every recipe in the message must have the same recipe type.

        :param recipe_id: The root recipe ID
        :type recipe_id: int
        """

        self._root_recipe_ids.append(root_recipe_id)

    def can_fit_more(self):
        """Indicates whether more recipes can fit in this message

        :return: True if more recipes can fit, False otherwise
        :rtype: bool
        """

        return len(self._root_recipe_ids) < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        json_dict = {'root_recipe_ids': self._root_recipe_ids, 'revision_id': self.revision_id,
                     'all_jobs': self.all_jobs, 'event_id': self.event_id, 'job_names': self.job_names}
        if self.batch_id is not None:
            json_dict['batch_id'] = self.batch_id

        return json_dict

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = ReprocessRecipes()
        message.all_jobs = json_dict['all_jobs']
        message.event_id = json_dict['event_id']
        message.job_names = json_dict['job_names']
        message.revision_id = json_dict['revision_id']
        for root_recipe_id in json_dict['root_recipe_ids']:
            message.add_recipe(root_recipe_id)
        if 'batch_id' in json_dict:
            message.batch_id = json_dict['batch_id']

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        when = now()
        msg_already_run = False

        with transaction.atomic():
            # Lock recipes
            superseded_recipes = Recipe.objects.get_locked_recipes_from_root_old(self._root_recipe_ids,
                                                                                 event_id=self.event_id)

            if not superseded_recipes:
                # The database transaction has already been completed, just need to resend messages
                logger.warning('This database transaction appears to have already been executed, will resend messages')
                msg_already_run = True
                recipes = Recipe.objects.filter(root_superseded_recipe_id__in=self._root_recipe_ids,
                                                event_id=self.event_id)
                superseded_recipes = Recipe.objects.get_locked_recipes([r.superseded_recipe_id for r in recipes])

            # Get revisions and filter out invalid recipes (wrong recipe type)
            revisions = RecipeTypeRevision.objects.get_revisions_for_reprocess_old(superseded_recipes, self.revision_id)
            recipe_type = revisions.values()[0].recipe_type
            superseded_recipes = [recipe for recipe in superseded_recipes if recipe.recipe_type_id == recipe_type.id]
            if len(superseded_recipes) < len(self._root_recipe_ids):
                diff = len(self._root_recipe_ids) - len(superseded_recipes)
                logger.warning('%d invalid recipes have been filtered out', diff)

            # Create new recipes and supersede old recipes
            if not msg_already_run:
                recipes = Recipe.objects.create_recipes_for_reprocess(recipe_type, revisions, superseded_recipes,
                                                                      self.event_id, batch_id=self.batch_id)
                Recipe.objects.bulk_create(recipes)
                logger.info('Created %d new recipe(s)', len(recipes))
                Recipe.objects.supersede_recipes([recipe.id for recipe in superseded_recipes], when)
                logger.info('Superseded %d old recipe(s)', len(recipes))

            # Handle superseded recipe jobs
            recipe_job_ids = RecipeNode.objects.get_recipe_job_ids([recipe.id for recipe in superseded_recipes])
            messages = self._handle_recipe_jobs(msg_already_run, recipes, self.revision_id, revisions, recipe_job_ids,
                                                self.job_names, self.all_jobs, when)
            self.new_messages.extend(messages)

        # Create messages to handle new recipes
        self.new_messages.extend(create_process_recipe_input_messages([recipe.id for recipe in recipes]))

        return True

    def _handle_recipe_jobs(self, msg_already_run, recipes, new_revision_id, revisions, recipe_job_ids, job_names,
                            all_jobs, when):
        """Handles the reprocessing of the recipe jobs

        :param msg_already_run: Whether the database transaction has already occurred
        :type msg_already_run: bool
        :param recipes: The new recipe models
        :type recipes: list
        :param new_revision_id: The ID of the new recipe type revision to use for reprocessing
        :type new_revision_id: int
        :param revisions: Recipe type revisions stored by revision ID
        :type revisions: dict
        :param recipe_job_ids: Dict where recipe ID maps to a dict where job_name maps to a list of job IDs
        :type recipe_job_ids: dict
        :param job_names: The job names within the recipes to force reprocess
        :type job_names: list
        :param all_jobs: If True then all jobs within the recipe should be reprocessed, False otherwise
        :type all_jobs: bool
        :param when: The time that the jobs were superseded
        :type when: :class:`datetime.datetime`
        :return: A list of messages that should be sent regarding the superseded jobs
        :rtype: list
        """

        superseded_job_ids = []
        unpublish_job_ids = []
        recipe_job_models = []
        recipe_job_count = 0
        new_graph = revisions[new_revision_id].get_recipe_definition().get_graph()

        for recipe in recipes:
            job_ids = recipe_job_ids[recipe.superseded_recipe_id]  # Get job IDs for superseded recipe
            old_graph = revisions[recipe.recipe_type_rev_id].get_recipe_definition().get_graph()
            names = old_graph.get_topological_order() if all_jobs else job_names

            # Compute the job differences between recipe revisions (force reprocess for jobs in job_names)
            graph_delta = RecipeGraphDelta(old_graph, new_graph)
            for job_name in names:
                graph_delta.reprocess_identical_node(job_name)

            # Jobs that are identical from old recipe to new recipe are just copied to new recipe
            if not msg_already_run:
                for identical_job_name in graph_delta.get_identical_nodes():
                    if identical_job_name in job_ids:
                        for job_id in job_ids[identical_job_name]:
                            recipe_job = RecipeNode()
                            recipe_job.job_id = job_id
                            recipe_job.node_name = identical_job_name
                            recipe_job.recipe_id = recipe.id
                            recipe_job.is_original = False
                            recipe_job_count += 1
                            recipe_job_models.append(recipe_job)
                            if len(recipe_job_models) >= MODEL_BATCH_SIZE:
                                RecipeNode.objects.bulk_create(recipe_job_models)
                                recipe_job_models = []

            # Jobs that changed from old recipe to new recipe should be superseded
            for changed_job_name in graph_delta.get_changed_nodes():
                if changed_job_name in job_ids:
                    superseded_job_ids.extend(job_ids[changed_job_name])

            # Jobs that were deleted from old recipe to new recipe should be superseded and unpublished
            for deleted_job_name in graph_delta.get_deleted_nodes():
                if deleted_job_name in job_ids:
                    superseded_job_ids.extend(job_ids[deleted_job_name])
                    unpublish_job_ids.extend(job_ids[deleted_job_name])

        # Finish creating any remaining RecipeNode models
        if recipe_job_models and not msg_already_run:
            RecipeNode.objects.bulk_create(recipe_job_models)
        logger.info('Copied %d job(s) to the new recipe(s)', recipe_job_count)

        # Supersede recipe jobs that were not copied over to a new recipe
        if not msg_already_run:
            Job.objects.supersede_jobs(superseded_job_ids, when)
        logger.info('Superseded %d job(s)', len(superseded_job_ids))
        logger.info('Found %d job(s) that should be unpublished', len(unpublish_job_ids))

        # Create messages to unpublish and cancel jobs
        messages = create_cancel_jobs_messages(superseded_job_ids, when)
        messages.extend(create_unpublish_jobs_messages(unpublish_job_ids, when))
        return messages
