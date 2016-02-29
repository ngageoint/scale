# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduler',
            name='max_node_errors',
            field=models.FloatField(default=5.0),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='scheduler',
            name='node_error_period',
            field=models.IntegerField(default=1),
            preserve_default=True,
        ),
    ]
