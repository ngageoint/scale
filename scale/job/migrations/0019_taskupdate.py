# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0018_auto_20160804_1402'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskUpdate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('task_id', models.CharField(max_length=50)),
                ('status', models.CharField(max_length=50)),
                ('timestamp', models.DateTimeField(null=True, blank=True)),
                ('source', models.CharField(max_length=50, null=True, blank=True)),
                ('reason', models.CharField(max_length=50, null=True, blank=True)),
                ('message', models.TextField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('job_exe', models.ForeignKey(to='job.JobExecution', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'db_table': 'task_update',
            },
            bases=(models.Model,),
        ),
    ]
