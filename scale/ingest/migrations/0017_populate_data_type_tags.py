# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

def populate_data_type_tags(apps, schema_editor):
    # Go through all of the ScaleFile models and convert the data_type string into an array of tags
    Ingest = apps.get_model('ingest', 'Ingest')

    total_count = Ingest.objects.exclude(data_type=None).count()
    if not total_count:
        return

    print('\nCreating new data type tags: %i' % total_count)
    ingests = Ingest.objects.exclude(data_type=None).iterator()
    done_count = 0
    for i in ingests:
        save_data_type_tags(i)

        done_count += 1
        percent = (float(done_count) / float(total_count)) * 100.00
        print('Progress: %i/%i (%.2f%%)' % (done_count, total_count, percent))

    print ('Migration finished.')

def save_data_type_tags(ingest):
        tags = set()
        if ingest.data_type:
            ingest.data_type_tags = ingest.data_type.split(',')
            ingest.save()

class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0016_ingest_data_type_tags'),
    ]

    operations = [
        migrations.RunPython(populate_data_type_tags),
    ]
