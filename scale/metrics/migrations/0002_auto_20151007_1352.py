# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import metrics.models


class Migration(migrations.Migration):

    dependencies = [
        ('metrics', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='metricsjobtype',
            name='canceled_count',
            field=metrics.models.PlotIntegerField(help_text='Number of incomplete canceled jobs.', null=True, verbose_name='Canceled Count', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='completed_count',
            field=metrics.models.PlotIntegerField(help_text='Number of successfully completed jobs.', null=True, verbose_name='Completed Count', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='failed_count',
            field=metrics.models.PlotIntegerField(help_text='Number of incomplete failed jobs.', null=True, verbose_name='Failed Count', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='job_time_avg',
            field=metrics.models.PlotIntegerField(help_text='Average time spent running the job task.', null=True, verbose_name='Job Task Time (Avg)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='job_time_max',
            field=metrics.models.PlotIntegerField(help_text='Maximum time spent running the job task.', null=True, verbose_name='Job Task Time (Max)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='job_time_min',
            field=metrics.models.PlotIntegerField(help_text='Minimum time spent running the job task.', null=True, verbose_name='Job Task Time (Min)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='job_time_sum',
            field=metrics.models.PlotIntegerField(help_text='Total time spent running the job task.', null=True, verbose_name='Job Task Time (Sum)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='post_time_avg',
            field=metrics.models.PlotIntegerField(help_text='Average time spent finalizing the job task.', null=True, verbose_name='Post-task Time (Avg)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='post_time_max',
            field=metrics.models.PlotIntegerField(help_text='Maximum time spent finalizing the job task.', null=True, verbose_name='Post-task Time (Max)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='post_time_min',
            field=metrics.models.PlotIntegerField(help_text='Minimum time spent finalizing the job task.', null=True, verbose_name='Post-task Time (Min)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='post_time_sum',
            field=metrics.models.PlotIntegerField(help_text='Total time spent finalizing the job task.', null=True, verbose_name='Post-task Time (Sum)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='pre_time_avg',
            field=metrics.models.PlotIntegerField(help_text='Average time spent preparing the job task.', null=True, verbose_name='Pre-task Time (Avg)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='pre_time_max',
            field=metrics.models.PlotIntegerField(help_text='Maximum time spent preparing the job task.', null=True, verbose_name='Pre-task Time (Max)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='pre_time_min',
            field=metrics.models.PlotIntegerField(help_text='Minimum time spent preparing the job task.', null=True, verbose_name='Pre-task Time (Min)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='pre_time_sum',
            field=metrics.models.PlotIntegerField(help_text='Total time spent preparing the job task.', null=True, verbose_name='Pre-task Time (Sum)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='queue_time_avg',
            field=metrics.models.PlotIntegerField(help_text='Average time the job waited in the queue.', null=True, verbose_name='Queue Time (Avg)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='queue_time_max',
            field=metrics.models.PlotIntegerField(help_text='Maximum time the job waited in the queue.', null=True, verbose_name='Queue Time (Max)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='queue_time_min',
            field=metrics.models.PlotIntegerField(help_text='Minimum time the job waited in the queue.', null=True, verbose_name='Queue Time (Min)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='queue_time_sum',
            field=metrics.models.PlotIntegerField(help_text='Total time the job waited in the queue.', null=True, verbose_name='Queue Time (Sum)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='run_time_avg',
            field=metrics.models.PlotIntegerField(help_text='Average time spent running the pre, job, and post tasks.', null=True, verbose_name='Run Time (Avg)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='run_time_max',
            field=metrics.models.PlotIntegerField(help_text='Maximum time spent running the pre, job, and post tasks.', null=True, verbose_name='Run Time (Max)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='run_time_min',
            field=metrics.models.PlotIntegerField(help_text='Minimum time spent running the pre, job, and post tasks.', null=True, verbose_name='Run Time (Min)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='run_time_sum',
            field=metrics.models.PlotIntegerField(help_text='Total time spent running the pre, job, and post tasks.', null=True, verbose_name='Run Time (Sum)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='stage_time_avg',
            field=metrics.models.PlotIntegerField(help_text='Average overhead time spent managing tasks.', null=True, verbose_name='Stage Time (Avg)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='stage_time_max',
            field=metrics.models.PlotIntegerField(help_text='Maximum overhead time spent managing tasks.', null=True, verbose_name='Stage Time (Max)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='stage_time_min',
            field=metrics.models.PlotIntegerField(help_text='Minimum overhead time spent managing tasks.', null=True, verbose_name='Stage Time (Min)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='stage_time_sum',
            field=metrics.models.PlotIntegerField(help_text='Total overhead time spent managing tasks.', null=True, verbose_name='Stage Time (Sum)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='total_count',
            field=metrics.models.PlotIntegerField(help_text='Number of completed, failed, and canceled jobs.', null=True, verbose_name='Total Count', blank=True),
            preserve_default=True,
        ),
    ]
