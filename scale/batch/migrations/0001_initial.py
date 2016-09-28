# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgjson.fields
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trigger', '0004_auto_20151207_1215'),
        ('job', '0019_taskupdate'),
        ('recipe', '0014_auto_20160608_1402'),
    ]

    operations = [
        migrations.CreateModel(
            name='Batch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=50, null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('status', models.CharField(default='PENDING', max_length=50, db_index=True, choices=[('PENDING', 'PENDING'), ('QUEUED', 'QUEUED'), ('RUNNING', 'RUNNING'), ('FAILED', 'FAILED'), ('COMPLETED', 'COMPLETED'), ('CANCELED', 'CANCELED')])),
                ('definition', djorm_pgjson.fields.JSONField(default={}, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('completed', models.DateTimeField(null=True, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('event', models.ForeignKey(to='trigger.TriggerEvent', on_delete=django.db.models.deletion.PROTECT)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='job.Job', null=True)),
                ('recipe_type', models.ForeignKey(to='recipe.RecipeType', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'db_table': 'batch',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BatchJob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('batch', models.ForeignKey(to='batch.Batch', on_delete=django.db.models.deletion.PROTECT)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='job.Job', null=True)),
                ('superseded_job', models.ForeignKey(related_name='superseded_by_batch', on_delete=django.db.models.deletion.PROTECT, blank=True, to='job.Job', null=True)),
            ],
            options={
                'db_table': 'batch_job',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BatchRecipe',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('batch', models.ForeignKey(to='batch.Batch', on_delete=django.db.models.deletion.PROTECT)),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='recipe.Recipe', null=True)),
                ('superseded_recipe', models.ForeignKey(related_name='superseded_by_batch', on_delete=django.db.models.deletion.PROTECT, blank=True, to='recipe.Recipe', null=True)),
            ],
            options={
                'db_table': 'batch_recipe',
            },
            bases=(models.Model,),
        ),
    ]
