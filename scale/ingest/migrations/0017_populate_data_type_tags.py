# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import connection, migrations

def disable_indices(apps, schema_editor):
    print('%s: disabling indices for ingest' % datetime.datetime.now())
    update = 'UPDATE pg_index SET indisready=false, indisvalid=false WHERE indrelid = ( SELECT oid FROM pg_class WHERE relname=\'ingest\' )'
    with connection.cursor() as cursor:
        cursor.execute(update)
        count = cursor.rowcount
        if count:
            print('%d indices updated' % count)
    print('%s: finished disabling indices for ingest' % datetime.datetime.now())
    
def enable_indices(apps, schema_editor):
    print('%s: disabling indices for ingest' % datetime.datetime.now())
    update = 'UPDATE pg_index SET indisready=true, indisvalid=true WHERE indrelid = ( SELECT oid FROM pg_class WHERE relname=\'ingest\' )'
    with connection.cursor() as cursor:
        cursor.execute(update)
        count = cursor.rowcount
        if count:
            print('%d indices updated' % count)
    print('%s: finished enabling indices for ingest' % datetime.datetime.now())
    reindex = 'REINDEX ingest'
    with connection.cursor() as cursor:
        cursor.execute(reindex)
    print('%s: reindexed ingest' % datetime.datetime.now())
    
def populate_data_type_tags(apps, schema_editor):
    # Go through all of the Ingest models and convert the data_type string into an array of tags
    print('%s: updating data_type_tags for ingest' % datetime.datetime.now())
    update = 'UPDATE ingest SET data_type_tags = string_to_array(data_type,\',\') WHERE data_type <> \'\''
    with connection.cursor() as cursor:
        cursor.execute(update)
        count = cursor.rowcount
        if count:
            print('%d entries updated with data type tags' % count)
            
    print('%s: finsihed updating data_type_tags for ingest' % datetime.datetime.now())
    print ('Migration finished.')

class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0016_ingest_data_type_tags'),
    ]

    operations = [
        migrations.RunPython(disable_indices),
        migrations.RunPython(populate_data_type_tags),
        migrations.RunPython(enable_indices),
    ]
