# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import metrics.models


class Migration(migrations.Migration):

    dependencies = [
        ('metrics', '0006_metricserror'),
    ]

    operations = [
        migrations.AlterField(
            model_name='metricserror',
            name='total_count',
            field=metrics.models.PlotBigIntegerField(help_text='Number of jobs that failed with a particular error type.', null=True, verbose_name='Total Count', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsingest',
            name='deferred_count',
            field=metrics.models.PlotBigIntegerField(help_text='Number of files deferred (ignored) by the ingest process.', null=True, verbose_name='Deferred Count', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsingest',
            name='duplicate_count',
            field=metrics.models.PlotBigIntegerField(help_text='Number of files that were duplicates of previous ingests.', null=True, verbose_name='Duplicate Count', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsingest',
            name='errored_count',
            field=metrics.models.PlotBigIntegerField(help_text='Number of files that failed to ingest.', null=True, verbose_name='Errored Count', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsingest',
            name='ingest_time_sum',
            field=metrics.models.PlotBigIntegerField(help_text='Total time spent processing files during ingest.', null=True, verbose_name='Ingest Time (Sum)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsingest',
            name='ingested_count',
            field=metrics.models.PlotBigIntegerField(help_text='Number of files successfully ingested.', null=True, verbose_name='Ingested Count', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsingest',
            name='total_count',
            field=metrics.models.PlotBigIntegerField(help_text='Number of deferred, ingested, errored, and duplicate ingests.', null=True, verbose_name='Total Count', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsingest',
            name='transfer_time_sum',
            field=metrics.models.PlotBigIntegerField(help_text='Total time spent transferring files before ingest.', null=True, verbose_name='Transfer Time (Sum)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='canceled_count',
            field=metrics.models.PlotBigIntegerField(help_text='Number of incomplete canceled jobs.', null=True, verbose_name='Canceled Count', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='completed_count',
            field=metrics.models.PlotBigIntegerField(help_text='Number of successfully completed jobs.', null=True, verbose_name='Completed Count', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='error_algorithm_count',
            field=metrics.models.PlotBigIntegerField(help_text='Number of failed jobs due to an algorithm error.', null=True, verbose_name='Algorithm Error Count', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='error_data_count',
            field=metrics.models.PlotBigIntegerField(help_text='Number of failed jobs due to a data error.', null=True, verbose_name='Data Error Count', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='error_system_count',
            field=metrics.models.PlotBigIntegerField(help_text='Number of failed jobs due to a system error.', null=True, verbose_name='System Error Count', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='failed_count',
            field=metrics.models.PlotBigIntegerField(help_text='Number of incomplete failed jobs.', null=True, verbose_name='Failed Count', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='job_time_sum',
            field=metrics.models.PlotBigIntegerField(help_text='Total time spent running the job task.', null=True, verbose_name='Job Task Time (Sum)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='post_time_sum',
            field=metrics.models.PlotBigIntegerField(help_text='Total time spent finalizing the job task.', null=True, verbose_name='Post-task Time (Sum)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='pre_time_sum',
            field=metrics.models.PlotBigIntegerField(help_text='Total time spent preparing the job task.', null=True, verbose_name='Pre-task Time (Sum)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='queue_time_sum',
            field=metrics.models.PlotBigIntegerField(help_text='Total time the job waited in the queue.', null=True, verbose_name='Queue Time (Sum)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='run_time_sum',
            field=metrics.models.PlotBigIntegerField(help_text='Total time spent running the pre, job, and post tasks.', null=True, verbose_name='Run Time (Sum)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='stage_time_sum',
            field=metrics.models.PlotBigIntegerField(help_text='Total overhead time spent managing tasks.', null=True, verbose_name='Stage Time (Sum)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='metricsjobtype',
            name='total_count',
            field=metrics.models.PlotBigIntegerField(help_text='Number of completed, failed, and canceled jobs.', null=True, verbose_name='Total Count', blank=True),
            preserve_default=True,
        ),
    ]
