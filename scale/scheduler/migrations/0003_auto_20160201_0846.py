# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0002_auto_20151007_1352'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scheduler',
            name='max_node_errors',
            field=models.FloatField(default=50.0),
            preserve_default=True,
        ),
    ]
