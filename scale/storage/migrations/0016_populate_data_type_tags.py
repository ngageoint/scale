# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import connection, migrations

def disable_indices(apps, schema_editor):
    print('%s: disabling indices for scale_file' % datetime.datetime.now())
    update = 'UPDATE pg_index SET indisready=false, indisvalid=false WHERE indrelid = ( SELECT oid FROM pg_class WHERE relname=\'scale_file\' )'
    with connection.cursor() as cursor:
        cursor.execute(update)
        count = cursor.rowcount
        if count:
            print('%d indices updated' % count)
    print('%s: finished disabling indices for scale_file' % datetime.datetime.now())
    
def enable_indices(apps, schema_editor):
    print('%s: disabling indices for scale_file' % datetime.datetime.now())
    update = 'UPDATE pg_index SET indisready=true, indisvalid=true WHERE indrelid = ( SELECT oid FROM pg_class WHERE relname=\'scale_file\' )'
    with connection.cursor() as cursor:
        cursor.execute(update)
        count = cursor.rowcount
        if count:
            print('%d indices updated' % count)
    print('%s: finished enabling indices for scale_file' % datetime.datetime.now())
    reindex = 'REINDEX scale_file'
    with connection.cursor() as cursor:
        cursor.execute(reindex)
    print('%s: reindexed scale_file' % datetime.datetime.now())
    
def populate_data_type_tags(apps, schema_editor):
    # Go through all of the ScaleFile models and convert the data_type string into an array of tags
    print('%s: updating data_type_tags for scale_file' % datetime.datetime.now())
    update = 'UPDATE scale_file SET data_type_tags = string_to_array(data_type,\',\') WHERE data_type <> \'\''
    with connection.cursor() as cursor:
        cursor.execute(update)
        count = cursor.rowcount
        if count:
            print('%d entries updated with data type tags' % count)

    print('%s: finsihed updating data_type_tags for scale_file' % datetime.datetime.now())
    print ('Migration finished.')
            
def non_null_metadata(apps, schema_editor):
    ScaleFile = apps.get_model('storage', 'ScaleFile')
    
    # Capture Null values for the meta_data field
    print('Fixing null metadata...')
    
    ScaleFile.objects.filter(meta_data='null').update(meta_data={})
    ScaleFile.objects.filter(meta_data__isnull=True).update(meta_data={})
            
    print('Fixed null metadata')

class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0015_scalefile_data_type_tags'),
    ]

    operations = [
        migrations.RunPython(disable_indices),
        migrations.RunPython(non_null_metadata),
        migrations.RunPython(populate_data_type_tags),
        migrations.RunPython(enable_indices),
    ]
