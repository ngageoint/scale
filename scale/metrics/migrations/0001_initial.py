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
            name='MetricsJobType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('occurred', models.DateField(db_index=True)),
                ('completed_count', models.IntegerField(null=True, blank=True)),
                ('failed_count', models.IntegerField(null=True, blank=True)),
                ('canceled_count', models.IntegerField(null=True, blank=True)),
                ('total_count', models.IntegerField(null=True, blank=True)),
                ('queue_time_sum', models.IntegerField(null=True, blank=True)),
                ('queue_time_min', models.IntegerField(null=True, blank=True)),
                ('queue_time_max', models.IntegerField(null=True, blank=True)),
                ('queue_time_avg', models.IntegerField(null=True, blank=True)),
                ('pre_time_sum', models.IntegerField(null=True, blank=True)),
                ('pre_time_min', models.IntegerField(null=True, blank=True)),
                ('pre_time_max', models.IntegerField(null=True, blank=True)),
                ('pre_time_avg', models.IntegerField(null=True, blank=True)),
                ('job_time_sum', models.IntegerField(null=True, blank=True)),
                ('job_time_min', models.IntegerField(null=True, blank=True)),
                ('job_time_max', models.IntegerField(null=True, blank=True)),
                ('job_time_avg', models.IntegerField(null=True, blank=True)),
                ('post_time_sum', models.IntegerField(null=True, blank=True)),
                ('post_time_min', models.IntegerField(null=True, blank=True)),
                ('post_time_max', models.IntegerField(null=True, blank=True)),
                ('post_time_avg', models.IntegerField(null=True, blank=True)),
                ('run_time_sum', models.IntegerField(null=True, blank=True)),
                ('run_time_min', models.IntegerField(null=True, blank=True)),
                ('run_time_max', models.IntegerField(null=True, blank=True)),
                ('run_time_avg', models.IntegerField(null=True, blank=True)),
                ('stage_time_sum', models.IntegerField(null=True, blank=True)),
                ('stage_time_min', models.IntegerField(null=True, blank=True)),
                ('stage_time_max', models.IntegerField(null=True, blank=True)),
                ('stage_time_avg', models.IntegerField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('job_type', models.ForeignKey(to='job.JobType', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'db_table': 'metrics_job_type',
            },
            bases=(models.Model,),
        ),
    ]
