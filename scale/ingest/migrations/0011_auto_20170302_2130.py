# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0022_jobtype_configuration'),
        ('ingest', '0010_auto_20170206_1646'),
    ]

    operations = [
        migrations.AddField(
            model_name='scan',
            name='dry_run_job',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, blank=True, to='job.Job', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='scan',
            name='job',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.PROTECT, blank=True, to='job.Job', null=True),
            preserve_default=True,
        ),
    ]
