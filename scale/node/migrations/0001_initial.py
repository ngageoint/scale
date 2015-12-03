# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Node',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hostname', models.CharField(unique=True, max_length=250)),
                ('port', models.IntegerField()),
                ('slave_id', models.CharField(unique=True, max_length=250, db_index=True)),
                ('is_paused', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('archived', models.DateTimeField(null=True, blank=True)),
                ('last_offer', models.DateTimeField(null=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'node',
            },
            bases=(models.Model,),
        ),
    ]
