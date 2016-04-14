# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingest',
            name='strike',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, default=1, to='ingest.Strike'),
            preserve_default=False,
        ),
    ]
