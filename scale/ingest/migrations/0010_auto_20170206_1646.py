# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0009_scan'),
    ]

    operations = [
        migrations.AddField(
            model_name='ingest',
            name='scan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='ingest.Scan', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='ingest',
            name='strike',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='ingest.Strike', null=True),
            preserve_default=True,
        ),
    ]
