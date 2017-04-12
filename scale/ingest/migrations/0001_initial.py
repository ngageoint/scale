# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import util.deprecation
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0001_initial'),
        ('storage', '0001_initial'),
        ('source', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ingest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file_name', models.CharField(max_length=250, db_index=True)),
                ('status', models.CharField(default='TRANSFERRING', max_length=50, db_index=True, choices=[('TRANSFERRING', 'TRANSFERRING'), ('TRANSFERRED', 'TRANSFERRED'), ('DEFERRED', 'DEFERRED'), ('QUEUED', 'QUEUED'), ('INGESTING', 'INGESTING'), ('INGESTED', 'INGESTED'), ('ERRORED', 'ERRORED'), ('DUPLICATE', 'DUPLICATE')])),
                ('transfer_path', models.CharField(max_length=1000)),
                ('bytes_transferred', models.BigIntegerField()),
                ('transfer_started', models.DateTimeField()),
                ('transfer_ended', models.DateTimeField(null=True, blank=True)),
                ('media_type', models.CharField(max_length=250, blank=True)),
                ('file_size', models.BigIntegerField(null=True, blank=True)),
                ('data_type', models.TextField(blank=True)),
                ('file_path', models.CharField(max_length=1000, blank=True)),
                ('ingest_path', models.CharField(max_length=1000, blank=True)),
                ('ingest_started', models.DateTimeField(null=True, blank=True)),
                ('ingest_ended', models.DateTimeField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('job', models.ForeignKey(blank=True, to='job.Job', null=True)),
                ('source_file', models.ForeignKey(blank=True, to='source.SourceFile', null=True)),
            ],
            options={
                'db_table': 'ingest',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Strike',
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
                'db_table': 'strike',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='ingest',
            name='strike',
            field=models.ForeignKey(blank=True, to='ingest.Strike', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='ingest',
            name='workspace',
            field=models.ForeignKey(blank=True, to='storage.Workspace', null=True),
            preserve_default=True,
        ),
    ]
