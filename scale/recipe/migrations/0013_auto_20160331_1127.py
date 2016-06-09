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
        total_count = RecipeJobOld.objects.all().count()
        print 'Populating new recipe_job table: %s rows' % str(total_count)
        done_count = 0
        batch_size = 500
        while done_count < total_count:
            percent = (float(done_count) / float(total_count)) * 100.00
            print 'Completed %s of %s recipe jobs (%f%%)' % (done_count, total_count, percent)
            batch_end = done_count + batch_size
            for recipe_job_old in RecipeJobOld.objects.all().order_by('job_id')[done_count:batch_end]:
                recipe_job = RecipeJob()
                recipe_job.recipe_id = recipe_job_old.recipe_id
                recipe_job.job_id = recipe_job_old.job_id
                recipe_job.job_name = recipe_job_old.job_name
                recipe_jobs_to_create.append(recipe_job)
            RecipeJob.objects.bulk_create(recipe_jobs_to_create)
            recipe_jobs_to_create = []
            done_count += batch_size
        print 'All %s recipe jobs completed' % str(total_count)
        old_count = RecipeJobOld.objects.all().count()
        new_count = RecipeJob.objects.all().count()
        if old_count != new_count:
            raise Exception('Failed conversion: There are %s old recipe job models and %s new recipe models',
                            str(old_count), str(new_count))

    operations = [
        migrations.RunPython(populate_recipe_job),
    ]
