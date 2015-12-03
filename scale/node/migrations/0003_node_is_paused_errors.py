# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('node', '0002_node_pause_reason'),
    ]

    operations = [
        migrations.AddField(
            model_name='node',
            name='is_paused_errors',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
