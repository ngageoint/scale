# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import util.deprecation
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0022_jobtype_configuration'),
        ('ingest', '0008_auto_20170127_1332'),
    ]

    operations = [
        migrations.CreateModel(
            name='Scan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('title', models.CharField(max_length=50, null=True, blank=True)),
                ('description', models.CharField(max_length=500, blank=True)),
                ('configuration', util.deprecation.JSONStringField(default={}, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='job.Job', null=True)),
            ],
            options={
                'db_table': 'scan',
            },
            bases=(models.Model,),
        ),
    ]
