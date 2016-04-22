# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import metrics.models


class Migration(migrations.Migration):

    dependencies = [
        ('error', '0003_error_is_builtin'),
        ('metrics', '0005_auto_20160415_1636'),
    ]

    operations = [
        migrations.CreateModel(
            name='MetricsError',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('occurred', models.DateField(db_index=True)),
                ('total_count', metrics.models.PlotIntegerField(help_text='Number of jobs that failed with a particular error type.', null=True, verbose_name='Total Count', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('error', models.ForeignKey(to='error.Error', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'db_table': 'metrics_error',
            },
            bases=(models.Model,),
        ),
    ]
