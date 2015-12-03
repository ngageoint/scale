# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Error',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50, db_index=True)),
                ('title', models.CharField(max_length=50, null=True, blank=True)),
                ('description', models.CharField(max_length=250)),
                ('category', models.CharField(default='SYSTEM', max_length=50, db_index=True, choices=[('SYSTEM', 'SYSTEM'), ('ALGORITHM', 'ALGORITHM'), ('DATA', 'DATA')])),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'error',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LogEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('host', models.CharField(max_length=128)),
                ('level', models.CharField(max_length=32)),
                ('message', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('stacktrace', models.TextField(null=True)),
            ],
            options={
                'db_table': 'logentry',
            },
            bases=(models.Model,),
        ),
    ]
