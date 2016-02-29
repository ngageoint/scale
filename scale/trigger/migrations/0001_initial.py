# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgjson.fields
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TriggerEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=50, db_index=True)),
                ('description', djorm_pgjson.fields.JSONField(default={}, null=True, blank=True)),
                ('occurred', models.DateTimeField(db_index=True)),
            ],
            options={
                'db_table': 'trigger_event',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TriggerRule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('type', models.CharField(max_length=50, db_index=True)),
                ('title', models.CharField(max_length=50, null=True, blank=True)),
                ('description', models.CharField(max_length=250, null=True, blank=True)),
                ('configuration', djorm_pgjson.fields.JSONField(default={}, null=True, blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('archived', models.DateTimeField(null=True, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'trigger_rule',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='triggerevent',
            name='rule',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='trigger.TriggerRule', null=True),
            preserve_default=True,
        ),
    ]
