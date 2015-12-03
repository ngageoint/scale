# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0003_auto_20151016_0849'),
        ('queue', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobLoad',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('measured', models.DateTimeField(db_index=True)),
                ('pending_count', models.IntegerField()),
                ('queued_count', models.IntegerField()),
                ('running_count', models.IntegerField()),
                ('total_count', models.IntegerField()),
                ('job_type', models.ForeignKey(to='job.JobType', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'db_table': 'job_load',
            },
            bases=(models.Model,),
        ),
    ]
