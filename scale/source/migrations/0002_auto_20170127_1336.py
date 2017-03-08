# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import connection, models, migrations


def copy_source_file(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute('SELECT * INTO source_file_temp FROM source_file')


class Migration(migrations.Migration):

    dependencies = [
        ('source', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(copy_source_file),
    ]
