"""Defines a command message that purges a source file"""
from __future__ import unicode_literals

import logging

from ingest.models import Ingest
from job.messages.spawn_delete_files_job import create_spawn_delete_files_job
from job.models import JobInputFile
from messaging.messages.message import CommandMessage
from recipe.messages.purge_recipe import create_purge_recipe
from recipe.models import RecipeInputFile
from storage.models import ScaleFile


logger = logging.getLogger(__name__)


def create_purge_source_file_message(source_file_id, trigger_id, purge):
    """Creates messages to removes a source file form Scale

    :param source_file_id: The source file ID
    :type source_file_id: int
    :param trigger_id: The trigger event ID for the purge operation
    :type trigger_id: int
    :param purge: Boolean value to determine if the files should be purged
    :type purge: bool
    :return: The purge source file message
    :rtype: :class:`storage.messages.purge_source_file.PurgeSourceFile`
    """

    message = PurgeSourceFile()
    message.source_file_id = source_file_id
    message.trigger_id = trigger_id
    message.purge = purge

    return message


class PurgeSourceFile(CommandMessage):
    """Command message that removes source file models
    """

    def __init__(self):
        """Constructor
        """

        super(PurgeSourceFile, self).__init__('purge_source_file')

        self.source_file_id = None
        self.trigger_id = None
        self.purge = False


    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'source_file_id': self.source_file_id, 'trigger_id': self.trigger_id, 'purge': str(self.purge)}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = PurgeSourceFile()
        message.source_file_id = json_dict['source_file_id']
        message.trigger_id = json_dict['trigger_id']
        message.purge = bool(json_dict['purge'])

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        jobs = JobInputFile.objects.filter(input_file=self.source_file_id,
                                           job__recipe__isnull=True).select_related('job')
        recipes = RecipeInputFile.objects.filter(input_file=self.source_file_id,
                                                 recipe__is_superseded=False).select_related('recipe')

        # Kick off spawn_delete_job_files for jobs that are not in a recipe and have given source_file as input
        for job in jobs:
            self.new_messages.extend(create_spawn_delete_files_job(job_id=job.id,
                                                                   trigger_id=self.trigger_id,
                                                                   purge=self.purge))

        # Kick off purge_recipe for recipes that are not superseded and have the given source_file as input
        for recipe in recipes:
            self.new_messages.extend(create_purge_recipe(recipe_id=recipe.id, trigger_id=self.trigger_id))

        # Delete Ingest and ScaleFile models for the given source_file
        if not jobs and not recipes:
            Ingest.objects.filter(source_file__id=self.source_file_id).delete()
            ScaleFile.objects.filter(id=self.source_file_id).delete()

        return True
