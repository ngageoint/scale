# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0019_taskupdate'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='jobexecution',
            name='cleanup_job',
        ),
        migrations.RemoveField(
            model_name='jobexecution',
            name='requires_cleanup',
        ),
        migrations.RemoveField(
            model_name='jobtype',
            name='requires_cleanup',
        ),
        migrations.AddField(
            model_name='jobexecution',
            name='cluster_id',
            field=models.CharField(max_length=100, null=True, blank=True),
            preserve_default=True,
        ),
    ]
