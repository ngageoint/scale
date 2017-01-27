# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import connection, models, migrations


def delete_constraint(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute('ALTER TABLE "ingest" DROP CONSTRAINT "ingest_source_file_id_67e3c0c9_fk_source_file_file_id"')


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0006_auto_20161202_1621'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingest',
            name='source_file',
            field=models.ForeignKey(db_constraint=False, blank=True, to='source.SourceFile', null=True),
            preserve_default=True,
        ),
        migrations.RunPython(delete_constraint),
    ]
