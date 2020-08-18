# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2019-01-26 23:33
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0014_auto_20170412_1225'),
    ]

    operations = [
        migrations.CreateModel(
            name='IngestEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(db_index=True, max_length=50)),
                ('description', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('occurred', models.DateTimeField(db_index=True)),
                ('ingest', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='ingest.Ingest')),
                ('scan', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='ingest.Scan')),
                ('strike', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='ingest.Strike')),
            ],
            options={
                'db_table': 'ingest_event',
            },
        ),
    ]