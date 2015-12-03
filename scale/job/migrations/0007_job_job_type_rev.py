# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0006_auto_20151106_1608'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='job_type_rev',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, default=1, to='job.JobTypeRevision'),
            preserve_default=False,
        ),
    ]
