# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgjson.fields


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
            field=djorm_pgjson.fields.JSONField(default={}, null=True, blank=True),
            preserve_default=True,
        ),
    ]
