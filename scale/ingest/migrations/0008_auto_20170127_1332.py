# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0007_auto_20170127_1327'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingest',
            name='source_file',
            field=models.ForeignKey(blank=True, to='storage.ScaleFile', null=True),
            preserve_default=True,
        ),
    ]
