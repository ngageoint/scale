# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0007_fileancestrylink_batch'),
    ]

    def populate_file_ancestry_link_batch(apps, schema_editor):
        # Go through all of the BatchRecipe models and update the corresponding FileAncestryLink models
        BatchRecipe = apps.get_model('batch', 'BatchRecipe')
        FileAncestryLink = apps.get_model('product', 'FileAncestryLink')
        total_count = BatchRecipe.objects.all().count()
        print 'Populating new batch field for %s batch_recipe rows' % str(total_count)
        done_count = 0
        for batch_recipe in BatchRecipe.objects.all():
            percent = (float(done_count) / float(total_count)) * 100.00
            print 'Completed %s of %s batch_recipe rows (%f%%)' % (done_count, total_count, percent)
            FileAncestryLink.objects.filter(recipe_id=batch_recipe.recipe_id).update(batch_id=batch_recipe.batch_id)
            done_count += 1
        print 'All %s batch_recipe rows completed' % str(total_count)

    operations = [
        migrations.RunPython(populate_file_ancestry_link_batch),
    ]
