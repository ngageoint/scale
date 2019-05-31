# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0007_fileancestrylink_batch'),
    ]

    def populate_file_ancestry_link_batch(apps, schema_editor):
        # Go through all of the BatchRecipe models and update the corresponding FileAncestryLink models
        Recipe = apps.get_model('recipe', 'Recipe')
        FileAncestryLink = apps.get_model('product', 'FileAncestryLink')
        total_count = Recipe.objects.all().count()
        print 'Populating new batch field for %s recipe rows' % str(total_count)
        done_count = 0
        for recipe in Recipe.objects.all():
            percent = (float(done_count) / float(total_count)) * 100.00
            print 'Completed %s of %s recipe rows (%f%%)' % (done_count, total_count, percent)
            FileAncestryLink.objects.filter(recipe_id=recipe.id).update(batch_id=recipe.batch_id)
            done_count += 1
        print 'All %s batch_recipe rows completed' % str(total_count)

    operations = [
        migrations.RunPython(populate_file_ancestry_link_batch),
    ]
