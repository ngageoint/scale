# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import metrics.models


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0001_initial'),
        ('metrics', '0002_auto_20151007_1352'),
    ]

    operations = [
        migrations.CreateModel(
            name='MetricsIngest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('occurred', models.DateField(db_index=True)),
                ('deferred_count', metrics.models.PlotIntegerField(help_text='Number of files deferred (ignored) by the ingest process.', null=True, verbose_name='Deferred Count', blank=True)),
                ('ingested_count', metrics.models.PlotIntegerField(help_text='Number of files successfully ingested.', null=True, verbose_name='Ingested Count', blank=True)),
                ('errored_count', metrics.models.PlotIntegerField(help_text='Number of files that failed to ingest.', null=True, verbose_name='Errored Count', blank=True)),
                ('duplicate_count', metrics.models.PlotIntegerField(help_text='Number of files that were duplicates of previous ingests.', null=True, verbose_name='Duplicate Count', blank=True)),
                ('total_count', metrics.models.PlotIntegerField(help_text='Number of deferred, ingested, errored, and duplicate ingests.', null=True, verbose_name='Total Count', blank=True)),
                ('file_size_sum', metrics.models.PlotIntegerField(help_text='Total size of ingested files.', null=True, verbose_name='File Size (Sum)', blank=True)),
                ('file_size_min', metrics.models.PlotIntegerField(help_text='Minimum size of ingested files.', null=True, verbose_name='File Size (Min)', blank=True)),
                ('file_size_max', metrics.models.PlotIntegerField(help_text='Maximum size of ingested files.', null=True, verbose_name='File Size (Max)', blank=True)),
                ('file_size_avg', metrics.models.PlotIntegerField(help_text='Average size of ingested files.', null=True, verbose_name='File Size (Avg)', blank=True)),
                ('transfer_time_sum', metrics.models.PlotIntegerField(help_text='Total time spent transferring files before ingest.', null=True, verbose_name='Transfer Time (Sum)', blank=True)),
                ('transfer_time_min', metrics.models.PlotIntegerField(help_text='Minimum time spent transferring files before ingest.', null=True, verbose_name='Transfer Time (Min)', blank=True)),
                ('transfer_time_max', metrics.models.PlotIntegerField(help_text='Maximum time spent transferring files before ingest.', null=True, verbose_name='Transfer Time (Max)', blank=True)),
                ('transfer_time_avg', metrics.models.PlotIntegerField(help_text='Average time spent transferring files before ingest.', null=True, verbose_name='Transfer Time (Avg)', blank=True)),
                ('ingest_time_sum', metrics.models.PlotIntegerField(help_text='Total time spent processing files during ingest.', null=True, verbose_name='Ingest Time (Sum)', blank=True)),
                ('ingest_time_min', metrics.models.PlotIntegerField(help_text='Minimum time spent processing files during ingest.', null=True, verbose_name='Ingest Time (Min)', blank=True)),
                ('ingest_time_max', metrics.models.PlotIntegerField(help_text='Maximum time spent processing files during ingest.', null=True, verbose_name='Ingest Time (Max)', blank=True)),
                ('ingest_time_avg', metrics.models.PlotIntegerField(help_text='Average time spent processing files during ingest.', null=True, verbose_name='Ingest Time (Avg)', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('strike', models.ForeignKey(to='ingest.Strike', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'db_table': 'metrics_ingest',
            },
            bases=(models.Model,),
        ),
    ]
