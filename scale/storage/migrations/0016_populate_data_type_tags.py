# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import connection, migrations

def populate_data_type_tags(apps, schema_editor):
    # Go through all of the ScaleFile models and convert the data_type string into an array of tags
    update = 'UPDATE scale_file SET data_type_tags = string_to_array(data_type,",") WHERE data_type <> \'\''
    with connection.cursor() as cursor:
        cursor.execute(update)
        count = cursor.rowcount
        if count:
            print('%d entries updated with data type tags' % count)

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
        migrations.RunPython(non_null_metadata),
        migrations.RunPython(populate_data_type_tags),
    ]
