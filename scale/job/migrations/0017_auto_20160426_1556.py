# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgjson.fields


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0016_auto_20160421_1553'),
        ('queue', '0008_auto_20160421_1648'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='jobexecution',
            name='docker_params',
        ),
        migrations.RemoveField(
            model_name='jobexecution',
            name='job_task_id',
        ),
        migrations.RemoveField(
            model_name='jobexecution',
            name='post_task_id',
        ),
        migrations.RemoveField(
            model_name='jobexecution',
            name='pre_task_id',
        ),
        migrations.AddField(
            model_name='jobexecution',
            name='configuration',
            field=djorm_pgjson.fields.JSONField(default={}, null=True, blank=True),
            preserve_default=True,
        ),
    ]
