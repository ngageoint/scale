# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import metrics.models


class Migration(migrations.Migration):

    dependencies = [
        ('metrics', '0003_metricsingest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='metricsingest',
            name='file_size_avg',
            field=metrics.models.PlotBigIntegerField(help_text='Average size of ingested files.', null=True, verbose_name='File Size (Avg)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsingest',
            name='file_size_max',
            field=metrics.models.PlotBigIntegerField(help_text='Maximum size of ingested files.', null=True, verbose_name='File Size (Max)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsingest',
            name='file_size_min',
            field=metrics.models.PlotBigIntegerField(help_text='Minimum size of ingested files.', null=True, verbose_name='File Size (Min)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsingest',
            name='file_size_sum',
            field=metrics.models.PlotBigIntegerField(help_text='Total size of ingested files.', null=True, verbose_name='File Size (Sum)', blank=True),
            preserve_default=True,
        ),
    ]
