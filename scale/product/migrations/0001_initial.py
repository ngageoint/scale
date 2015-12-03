# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0001_initial'),
        ('storage', '0001_initial'),
        ('recipe', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FileAncestryLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'file_ancestry_link',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductFile',
            fields=[
                ('file', models.OneToOneField(parent_link=True, primary_key=True, serialize=False, to='storage.ScaleFile')),
                ('is_operational', models.BooleanField(default=True)),
                ('has_been_published', models.BooleanField(default=False)),
                ('is_published', models.BooleanField(default=False)),
                ('published', models.DateTimeField(null=True, blank=True)),
                ('unpublished', models.DateTimeField(null=True, blank=True)),
                ('job', models.ForeignKey(to='job.Job', on_delete=django.db.models.deletion.PROTECT)),
                ('job_exe', models.ForeignKey(to='job.JobExecution', on_delete=django.db.models.deletion.PROTECT)),
                ('job_type', models.ForeignKey(to='job.JobType', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'db_table': 'product_file',
            },
            bases=('storage.scalefile',),
        ),
        migrations.AddField(
            model_name='fileancestrylink',
            name='ancestor',
            field=models.ForeignKey(related_name='descendants', on_delete=django.db.models.deletion.PROTECT, to='storage.ScaleFile'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fileancestrylink',
            name='ancestor_job',
            field=models.ForeignKey(related_name='ancestor_file_links', on_delete=django.db.models.deletion.PROTECT, blank=True, to='job.Job', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fileancestrylink',
            name='ancestor_job_exe',
            field=models.ForeignKey(related_name='ancestor_file_links', on_delete=django.db.models.deletion.PROTECT, blank=True, to='job.JobExecution', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fileancestrylink',
            name='descendant',
            field=models.ForeignKey(related_name='ancestors', on_delete=django.db.models.deletion.PROTECT, blank=True, to='product.ProductFile', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fileancestrylink',
            name='job',
            field=models.ForeignKey(related_name='file_links', on_delete=django.db.models.deletion.PROTECT, to='job.Job'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fileancestrylink',
            name='job_exe',
            field=models.ForeignKey(related_name='file_links', on_delete=django.db.models.deletion.PROTECT, to='job.JobExecution'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fileancestrylink',
            name='recipe',
            field=models.ForeignKey(related_name='file_links', on_delete=django.db.models.deletion.PROTECT, blank=True, to='recipe.Recipe', null=True),
            preserve_default=True,
        ),
    ]
