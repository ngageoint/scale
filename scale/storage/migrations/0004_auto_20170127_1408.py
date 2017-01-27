# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0006_auto_20170127_1348'),
        ('source', '0003_auto_20170127_1342'),
        ('job', '0022_jobtype_configuration'),
        ('storage', '0003_auto_20161202_1621'),
    ]

    operations = [
        migrations.AddField(
            model_name='scalefile',
            name='file_type',
            field=models.CharField(default='SOURCE', max_length=50, choices=[('SOURCE', 'SOURCE'), ('PRODUCT', 'PRODUCT')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='scalefile',
            name='has_been_published',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='scalefile',
            name='is_operational',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='scalefile',
            name='is_parsed',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='scalefile',
            name='is_published',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='scalefile',
            name='is_superseded',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='scalefile',
            name='job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='job.Job', null=True, db_index=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='scalefile',
            name='job_exe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='job.JobExecution', null=True, db_index=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='scalefile',
            name='job_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='job.JobType', null=True, db_index=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='scalefile',
            name='parsed',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='scalefile',
            name='published',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='scalefile',
            name='superseded',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='scalefile',
            name='unpublished',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
