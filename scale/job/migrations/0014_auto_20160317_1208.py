# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0013_auto_20160316_1805'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='delete_superseded',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='job',
            name='is_superseded',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='job',
            name='root_superseded_job',
            field=models.ForeignKey(related_name='superseded_by_jobs', on_delete=django.db.models.deletion.PROTECT, blank=True, to='job.Job', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='job',
            name='superseded',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='job',
            name='superseded_job',
            field=models.OneToOneField(related_name='superseded_by_job', null=True, on_delete=django.db.models.deletion.PROTECT, blank=True, to='job.Job'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='job',
            name='last_modified',
            field=models.DateTimeField(auto_now=True),
            preserve_default=True,
        ),
        migrations.AlterIndexTogether(
            name='job',
            index_together=set([('last_modified', 'job_type', 'status')]),
        ),
    ]
