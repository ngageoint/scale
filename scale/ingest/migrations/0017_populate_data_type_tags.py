# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import connection, migrations

def populate_data_type_tags(apps, schema_editor):
    # Go through all of the Ingest models and convert the data_type string into an array of tags
    
    update = 'UPDATE ingest SET data_type_tags = string_to_array(data_type,",") WHERE data_type <> \'\''
    with connection.cursor() as cursor:
        cursor.execute(update)
        count = cursor.rowcount
        if count:
            print('%d entries updated with data type tags' % count)

    print ('Migration finished.')

class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0016_ingest_data_type_tags'),
    ]

    operations = [
        migrations.RunPython(populate_data_type_tags),
    ]
