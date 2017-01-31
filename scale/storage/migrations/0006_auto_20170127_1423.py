# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0005_auto_20170127_1412'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scalefile',
            name='file_type',
            field=models.CharField(default='SOURCE', max_length=50, db_index=True, choices=[('SOURCE', 'SOURCE'), ('PRODUCT', 'PRODUCT')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='scalefile',
            name='job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='job.Job', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='scalefile',
            name='job_exe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='job.JobExecution', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='scalefile',
            name='job_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='job.JobType', null=True),
            preserve_default=True,
        ),
    ]
