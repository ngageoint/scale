# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from recipe.configuration.data.recipe_data import RecipeData


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0002_workspace_is_move_enabled'),
        ('recipe', '0015_recipefile'),
    ]

    def populate_recipe_file(apps, schema_editor):
        # Go through all of the recipe models and create a recipe file model for each of the recipe input files
        Recipe = apps.get_model('recipe', 'Recipe')
        RecipeFile = apps.get_model('recipe', 'RecipeFile')
        ScaleFile = apps.get_model('storage', 'ScaleFile')

        total_count = Recipe.objects.all().count()
        if not total_count:
            return

        print('\nCreating new recipe_file table rows: %i' % total_count)
        done_count = 0
        fail_count = 0
        batch_size = 500
        while done_count < total_count:
            batch_end = done_count + batch_size

            # Build a unique list of all valid input file ids
            batch_file_ids = set()
            recipes = Recipe.objects.all().order_by('id')[done_count:batch_end]
            for recipe in recipes:
                batch_file_ids.update(RecipeData(recipe.data).get_input_file_ids())
            valid_file_ids = {scale_file.id for scale_file in ScaleFile.objects.filter(pk__in=batch_file_ids)}

            # Create a model for each recipe input file
            recipe_files = []
            for recipe in recipes:
                input_file_ids = RecipeData(recipe.data).get_input_file_ids()
                for input_file_id in input_file_ids:
                    if input_file_id in valid_file_ids:
                        recipe_file = RecipeFile()
                        recipe_file.recipe_id = recipe.id
                        recipe_file.scale_file_id = input_file_id
                        recipe_file.created = recipe.created
                        recipe_files.append(recipe_file)
                    else:
                        fail_count += 1
                        print('Failed recipe: %i -> file: %i' % (recipe.id, input_file_id))

            RecipeFile.objects.bulk_create(recipe_files)

            done_count += len(recipes)
            percent = (float(done_count) / float(total_count)) * 100.00
            print('Progress: %i/%i (%.2f%%)' % (done_count, total_count, percent))
        print ('Migration finished. Failed: %i' % fail_count)

    operations = [
        migrations.RunPython(populate_recipe_file),
    ]
