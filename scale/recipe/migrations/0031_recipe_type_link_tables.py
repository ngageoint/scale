# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0030_auto_20181018_1518'),
    ]

    def populate_recipe_type_link_tables(apps, schema_editor):
        # Go through all of the recipe type models and create links for their sub recipes and job types
        RecipeType = apps.get_model('job', 'JobType')
        RecipeType = apps.get_model('recipe', 'RecipeType')
        RecipeType = apps.get_model('recipe', 'RecipeTypeJobLink')
        RecipeType = apps.get_model('recipe', 'RecipeTypeSubLink')

        total_count = RecipeType.objects.all().count()
        if not total_count:
            return

        print('\nCreating new recipe link table rows: %i' % total_count)
        recipe_types = RecipeType.objects.all()
        done_count = 0
        fail_count = 0
        for rt in recipe_types:
            try:
                RecipeTypeJobLink.objects.create_recipe_type_job_links_from_definition(rt)
                RecipeTypeSubLink.objects.create_recipe_type_sub_links_from_definition(rt)
            except (JobType.DoesNotExist, RecipeType.DoesNotExist) as ex:
                fail_count += 1
                print ('Failed creating links for recipe type %i: %s' % (rt.id, ex))
            
            done_count += 1
            percent = (float(done_count) / float(total_count)) * 100.00
            print('Progress: %i/%i (%.2f%%)' % (i, total_count, percent))
            
        print ('Migration finished. Failed: %i' % fail_count)

    operations = [
        migrations.RunPython(populate_recipe_type_link_tables),
    ]
