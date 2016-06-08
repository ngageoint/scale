# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0012_auto_20160330_1659'),
    ]

    def populate_recipe_job(apps, schema_editor):
        # Go through all of the old recipe_job models and create new ones for the new schema
        RecipeJob = apps.get_model('recipe', 'RecipeJob')
        RecipeJobOld = apps.get_model('recipe', 'RecipeJobOld')
        recipe_jobs_to_create = []
        for recipe_job_old in RecipeJobOld.objects.all().iterator():
            recipe_job = RecipeJob()
            recipe_job.recipe_id = recipe_job_old.recipe_id
            recipe_job.job_id = recipe_job_old.job_id
            recipe_job.job_name = recipe_job_old.job_name
            recipe_jobs_to_create.append(recipe_job)
            if len(recipe_jobs_to_create) >= 500:
                RecipeJob.objects.bulk_create(recipe_jobs_to_create)
                recipe_jobs_to_create = []
        if recipe_jobs_to_create:
            RecipeJob.objects.bulk_create(recipe_jobs_to_create)
        old_count = RecipeJobOld.objects.all().count()
        new_count = RecipeJob.objects.all().count()
        if old_count != new_count:
            raise Exception('Failed conversion: There are %s old recipe job models and %s new recipe models',
                            str(old_count), str(new_count))

    operations = [
        migrations.RunPython(populate_recipe_job),
    ]
