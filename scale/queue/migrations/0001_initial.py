# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Queue',
            fields=[
                ('job_exe', models.ForeignKey(primary_key=True, on_delete=django.db.models.deletion.PROTECT, serialize=False, to='job.JobExecution')),
                ('is_job_type_paused', models.BooleanField(default=False)),
                ('priority', models.IntegerField(db_index=True)),
                ('cpus_required', models.FloatField()),
                ('mem_required', models.FloatField()),
                ('disk_in_required', models.FloatField()),
                ('disk_out_required', models.FloatField()),
                ('disk_total_required', models.FloatField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('queued', models.DateTimeField()),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('job_type', models.ForeignKey(to='job.JobType', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'db_table': 'queue',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QueueDepthByJobType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('depth_time', models.DateTimeField(db_index=True)),
                ('depth', models.IntegerField()),
                ('job_type', models.ForeignKey(to='job.JobType', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'db_table': 'queue_depth_job_type',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QueueDepthByPriority',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('priority', models.IntegerField()),
                ('depth_time', models.DateTimeField(db_index=True)),
                ('depth', models.IntegerField()),
            ],
            options={
                'db_table': 'queue_depth_priority',
            },
            bases=(models.Model,),
        ),
    ]
