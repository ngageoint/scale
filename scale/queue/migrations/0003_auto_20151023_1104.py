# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('queue', '0002_jobload'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobload',
            name='job_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='job.JobType', null=True),
            preserve_default=True,
        ),
    ]
