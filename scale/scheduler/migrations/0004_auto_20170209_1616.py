# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0003_auto_20160201_0846'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scheduler',
            name='max_node_errors',
        ),
        migrations.RemoveField(
            model_name='scheduler',
            name='node_error_period',
        ),
    ]
