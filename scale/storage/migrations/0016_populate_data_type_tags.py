# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

def populate_data_type_tags(apps, schema_editor):
    # Go through all of the ScaleFile models and convert the data_type string into an array of tags
    ScaleFile = apps.get_model('storage', 'ScaleFile')

    total_count = ScaleFile.objects.all().count()
    if not total_count:
        return

    print('\nCreating new data type tags: %i' % total_count)
    files = ScaleFile.objects.all()
    done_count = 0
    for f in files:
        tags = set()
        if f.data_type:
            for tag in f.data_type.split(','):
                tags.add(tag)
        f.data_type_tags = list(tags)
        f.save()

        done_count += 1
        percent = (float(done_count) / float(total_count)) * 100.00
        print('Progress: %i/%i (%.2f%%)' % (done_count, total_count, percent))

    print ('Migration finished.')


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0015_scalefile_data_type_tags'),
    ]

    operations = [
        migrations.RunPython(populate_data_type_tags),
    ]
