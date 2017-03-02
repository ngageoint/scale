# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0008_auto_20170221_1413'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fileancestrylink',
            name='ancestor_job',
            field=models.ForeignKey(related_name='ancestor_job_file_links', on_delete=django.db.models.deletion.PROTECT, blank=True, to='job.Job', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fileancestrylink',
            name='ancestor_job_exe',
            field=models.ForeignKey(related_name='ancestor_job_exe_file_links', on_delete=django.db.models.deletion.PROTECT, blank=True, to='job.JobExecution', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fileancestrylink',
            name='job',
            field=models.ForeignKey(related_name='job_file_links', on_delete=django.db.models.deletion.PROTECT, to='job.Job'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fileancestrylink',
            name='job_exe',
            field=models.ForeignKey(related_name='job_exe_file_links', on_delete=django.db.models.deletion.PROTECT, to='job.JobExecution'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='fileancestrylink',
            name='recipe',
            field=models.ForeignKey(related_name='recipe_file_links', on_delete=django.db.models.deletion.PROTECT, blank=True, to='recipe.Recipe', null=True),
            preserve_default=True,
        ),
    ]
