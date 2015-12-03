# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgjson.fields
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0005_auto_20151030_1402'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobTypeRevision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('revision_num', models.IntegerField()),
                ('interface', djorm_pgjson.fields.JSONField(default={}, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('job_type', models.ForeignKey(to='job.JobType', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'db_table': 'job_type_revision',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='jobtyperevision',
            unique_together=set([('job_type', 'revision_num')]),
        ),
    ]
