# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import metrics.models


class Migration(migrations.Migration):

    dependencies = [
        ('metrics', '0004_auto_20151104_1640'),
    ]

    operations = [
        migrations.AddField(
            model_name='metricsjobtype',
            name='error_algorithm_count',
            field=metrics.models.PlotIntegerField(help_text='Number of failed jobs due to an algorithm error.', null=True, verbose_name='Algorithm Error Count', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='metricsjobtype',
            name='error_data_count',
            field=metrics.models.PlotIntegerField(help_text='Number of failed jobs due to a data error.', null=True, verbose_name='Data Error Count', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='metricsjobtype',
            name='error_system_count',
            field=metrics.models.PlotIntegerField(help_text='Number of failed jobs due to a system error.', null=True, verbose_name='System Error Count', blank=True),
            preserve_default=True,
        ),
    ]
