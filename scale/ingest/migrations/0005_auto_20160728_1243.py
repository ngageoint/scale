# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0004_auto_20160711_1058'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingest',
            name='bytes_transferred',
            field=models.BigIntegerField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
