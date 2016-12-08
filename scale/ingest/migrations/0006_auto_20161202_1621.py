# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0005_auto_20160728_1243'),
    ]

    operations = [
        migrations.AddField(
            model_name='ingest',
            name='data_ended',
            field=models.DateTimeField(db_index=True, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='ingest',
            name='data_started',
            field=models.DateTimeField(db_index=True, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='ingest',
            name='ingest_ended',
            field=models.DateTimeField(db_index=True, null=True, blank=True),
            preserve_default=True,
        ),
    ]
