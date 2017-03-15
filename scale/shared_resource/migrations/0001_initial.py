# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import util.deprecation


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0001_initial'),
        ('node', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SharedResource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100, db_index=True)),
                ('title', models.CharField(max_length=100, null=True, blank=True)),
                ('description', models.CharField(max_length=250, null=True, blank=True)),
                ('limit', models.FloatField(null=True)),
                ('json_config', util.deprecation.JSONStringField(default={}, null=True, blank=True)),
                ('is_global', models.BooleanField(default=True)),
                ('nodes', models.ManyToManyField(to='node.Node')),
            ],
            options={
                'db_table': 'shared_resource',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SharedResourceRequirement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('usage', models.FloatField(null=True)),
                ('job_type', models.ForeignKey(to='job.JobType')),
                ('shared_resource', models.ForeignKey(to='shared_resource.SharedResource')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
