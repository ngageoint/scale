# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from django.db import migrations

def populate_data_type_tags(apps, schema_editor):
    # Go through all of the ScaleFile models and convert the data_type string into an array of tags
    ScaleFile = apps.get_model('storage', 'ScaleFile')

    total_count = ScaleFile.objects.exclude(data_type=None).count()
    if not total_count:
        return

    print('\nCreating new data type tags: %i' % total_count)
    files = ScaleFile.objects.exclude(data_type=None).iterator()
    done_count = 0
    for f in files:
        save_data_type_tags(f)

        done_count += 1
        percent = (float(done_count) / float(total_count)) * 100.00
        print('Progress: %i/%i (%.2f%%)' % (done_count, total_count, percent))

    print ('Migration finished.')

def save_data_type_tags(scale_file):
        tags = set()
        if scale_file.data_type:
            scale_file.data_type_tags = scale_file.data_type.split(',')
            scale_file.save()
            
def non_null_metadata(apps, schema_editor):
    ScaleFile = apps.get_model('storage', 'ScaleFile')
    
    # Capture Null values for the meta_data field
    
    files = ScaleFile.objects.all().iterator()
    for f in files:
        if not f.meta_data or f.meta_data == 'null':
            f.meta_data = json.dumps(dict)
            f.save()
            
    print('Migration finished')

class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0015_scalefile_data_type_tags'),
    ]

    operations = [
        migrations.RunPython(non_null_metadata),
        migrations.RunPython(populate_data_type_tags),
    ]
