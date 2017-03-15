# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import util.deprecation


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0014_auto_20160317_1208'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='job',
            name='docker_params',
        ),
        migrations.AddField(
            model_name='job',
            name='configuration',
            field=util.deprecation.JSONStringField(default={}, null=True, blank=True),
            preserve_default=True,
        ),
    ]
