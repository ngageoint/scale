from __future__ import unicode_literals

import django
from django.test import TestCase

from batch.test import utils as batch_test_utils
from job.models import Job, JobExecution, TaskUpdate
from job.test import utils as job_test_utils
from recipe.models import Recipe
from recipe.test import utils as recipe_test_utils
from scheduler.database.updater import DatabaseUpdater


class TestDatabaseUpdater(TestCase):

    fixtures = ['batch_job_types.json']

    def setUp(self):
        django.setup()

    def test_update_job_exe_dup(self):
        """Tests running the database update to remove job execution duplicates"""

        # Create jobs with duplicate job executions
        job_type = job_test_utils.create_job_type()
        job_1 = job_test_utils.create_job(job_type=job_type, num_exes=2)
        job_2 = job_test_utils.create_job(job_type=job_type, num_exes=3)
        job_3 = job_test_utils.create_job(job_type=job_type, num_exes=2)

        # Job 1
        job_exe_1 = job_test_utils.create_job_exe(job=job_1, status='COMPLETED', exe_num=1)
        job_exe_2 = job_test_utils.create_job_exe(job=job_1, status='COMPLETED', exe_num=1)
        job_exe_3 = job_test_utils.create_job_exe(job=job_1, status='COMPLETED', exe_num=2)
        job_exe_4 = job_test_utils.create_job_exe(job=job_1, status='COMPLETED', exe_num=2)

        # Job 2
        job_exe_5 = job_test_utils.create_job_exe(job=job_2, status='COMPLETED', exe_num=1)
        job_exe_6 = job_test_utils.create_job_exe(job=job_2, status='COMPLETED', exe_num=2)
        job_exe_7 = job_test_utils.create_job_exe(job=job_2, status='COMPLETED', exe_num=2)
        job_exe_8 = job_test_utils.create_job_exe(job=job_2, status='COMPLETED', exe_num=3)

        # Job 3
        job_exe_9 = job_test_utils.create_job_exe(job=job_3, status='COMPLETED', exe_num=1)

        # Create some task updates to make sure they get deleted as well
        task_updates = []
        task_updates.append(TaskUpdate(job_exe=job_exe_1, task_id='1234', status='foo'))
        task_updates.append(TaskUpdate(job_exe=job_exe_1, task_id='1234', status='foo'))
        task_updates.append(TaskUpdate(job_exe=job_exe_2, task_id='1234', status='foo'))
        task_updates.append(TaskUpdate(job_exe=job_exe_2, task_id='1234', status='foo'))
        task_updates.append(TaskUpdate(job_exe=job_exe_3, task_id='1234', status='foo'))
        task_updates.append(TaskUpdate(job_exe=job_exe_3, task_id='1234', status='foo'))
        task_updates.append(TaskUpdate(job_exe=job_exe_4, task_id='1234', status='foo'))
        task_updates.append(TaskUpdate(job_exe=job_exe_4, task_id='1234', status='foo'))
        TaskUpdate.objects.bulk_create(task_updates)

        # Run update
        updater = DatabaseUpdater()
        updater.update()

        expected_job_exe_ids = {job_exe_1.id, job_exe_3.id, job_exe_5.id, job_exe_6.id, job_exe_8.id, job_exe_9.id}
        actual_job_exe_ids = set()
        for job_exe in JobExecution.objects.all().only('id'):
            actual_job_exe_ids.add(job_exe.id)
        self.assertSetEqual(expected_job_exe_ids, actual_job_exe_ids)

    def test_update_recipe_fields(self):
        """Tests running the database update to populate new recipe fields in job model"""

        recipe_1 = recipe_test_utils.create_recipe(is_superseded=True)
        recipe_2 = recipe_test_utils.create_recipe()
        recipe_2.root_superseded_recipe = recipe_1
        recipe_2.superseded_recipe = recipe_1
        recipe_2.save()

        job_1 = job_test_utils.create_job()
        job_2 = job_test_utils.create_job(is_superseded=True)
        job_3 = job_test_utils.create_job()

        recipe_job_1 = recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_1)
        recipe_job_2 = recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_2)
        recipe_job_3 = recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_1)
        recipe_job_3.is_original = False
        recipe_job_4 = recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_3)

        # Run update
        updater = DatabaseUpdater()
        updater.update()

        # Check results
        job_1 = Job.objects.get(id=job_1.id)
        self.assertEqual(job_1.recipe_id, recipe_1.id)
        self.assertEqual(job_1.root_recipe_id, recipe_1.id)
        job_2 = Job.objects.get(id=job_2.id)
        self.assertEqual(job_2.recipe_id, recipe_1.id)
        self.assertEqual(job_2.root_recipe_id, recipe_1.id)
        job_3 = Job.objects.get(id=job_3.id)
        self.assertEqual(job_3.recipe_id, recipe_2.id)
        self.assertEqual(job_3.root_recipe_id, recipe_1.id)

    def test_update_batch_fields(self):
        """Tests running the database update to populate new batch fields in job and recipe models"""

        batch_1 = batch_test_utils.create_batch()
        batch_2 = batch_test_utils.create_batch()

        recipe_1 = recipe_test_utils.create_recipe()
        recipe_2 = recipe_test_utils.create_recipe()
        job_1 = job_test_utils.create_job()
        job_2 = job_test_utils.create_job()
        batch_test_utils.create_batch_recipe(batch=batch_1, recipe=recipe_1)
        batch_test_utils.create_batch_recipe(batch=batch_1, recipe=recipe_2)
        batch_test_utils.create_batch_job(batch=batch_1, job=job_1)
        batch_test_utils.create_batch_job(batch=batch_1, job=job_2)

        recipe_3 = recipe_test_utils.create_recipe()
        recipe_4 = recipe_test_utils.create_recipe()
        job_3 = job_test_utils.create_job()
        job_4 = job_test_utils.create_job()
        batch_test_utils.create_batch_recipe(batch=batch_2, recipe=recipe_3)
        batch_test_utils.create_batch_recipe(batch=batch_2, recipe=recipe_4)
        batch_test_utils.create_batch_job(batch=batch_2, job=job_3)
        batch_test_utils.create_batch_job(batch=batch_2, job=job_4)

        # Run update
        updater = DatabaseUpdater()
        updater.update()

        # Check results
        job_1 = Job.objects.get(id=job_1.id)
        self.assertEqual(job_1.batch_id, batch_1.id)
        job_2 = Job.objects.get(id=job_2.id)
        self.assertEqual(job_2.batch_id, batch_1.id)
        job_3 = Job.objects.get(id=job_3.id)
        self.assertEqual(job_3.batch_id, batch_2.id)
        job_4 = Job.objects.get(id=job_4.id)
        self.assertEqual(job_4.batch_id, batch_2.id)
        recipe_1 = Recipe.objects.get(id=recipe_1.id)
        self.assertEqual(recipe_1.batch_id, batch_1.id)
        recipe_2 = Recipe.objects.get(id=recipe_2.id)
        self.assertEqual(recipe_2.batch_id, batch_1.id)
        recipe_3 = Recipe.objects.get(id=recipe_3.id)
        self.assertEqual(recipe_3.batch_id, batch_2.id)
        recipe_4 = Recipe.objects.get(id=recipe_4.id)
        self.assertEqual(recipe_4.batch_id, batch_2.id)
