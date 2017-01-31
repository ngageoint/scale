# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import connection, models, migrations


def populate_scale_file(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute('UPDATE scale_file f SET is_parsed = s.is_parsed, parsed = s.parsed FROM source_file_temp s WHERE f.id = s.file_id')
        cursor.execute('UPDATE scale_file f SET file_type = \'PRODUCT\', job_exe_id = p.job_exe_id, job_id = p.job_id, job_type_id = p.job_type_id, is_operational = p.is_operational, has_been_published = p.has_been_published, is_published = p.is_published, is_superseded = p.is_superseded, published = p.published, unpublished = p.unpublished, superseded = p.superseded FROM product_file_temp p WHERE f.id = p.file_id')
        cursor.execute('DROP TABLE source_file_temp')
        cursor.execute('DROP TABLE product_file_temp')


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0004_auto_20170127_1408'),
    ]

    operations = [
        migrations.RunPython(populate_scale_file),
    ]
