from __future__ import unicode_literals

import copy
from datetime import timedelta

import django
from django.test import TestCase
from django.utils.timezone import now

from batch.definition.definition import BatchDefinition
from batch.test import utils as batch_test_utils
from batch.models import Batch
from job.models import Job, JobExecution, TaskUpdate
from job.test import utils as job_test_utils
from recipe.models import Recipe, RecipeTypeRevision
from recipe.test import utils as recipe_test_utils
from scheduler.database.updater import DatabaseUpdater


class TestDatabaseUpdater(TestCase):

    fixtures = ['batch_job_types.json']

    def setUp(self):
        django.setup()
