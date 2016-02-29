# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgjson.fields
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0001_initial'),
        ('trigger', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data', djorm_pgjson.fields.JSONField(default={}, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('completed', models.DateTimeField(null=True, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('event', models.ForeignKey(to='trigger.TriggerEvent', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'db_table': 'recipe',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RecipeJob',
            fields=[
                ('job', models.OneToOneField(primary_key=True, on_delete=django.db.models.deletion.PROTECT, serialize=False, to='job.Job')),
                ('job_name', models.CharField(max_length=100)),
                ('recipe', models.ForeignKey(to='recipe.Recipe', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'db_table': 'recipe_job',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RecipeType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50, db_index=True)),
                ('version', models.CharField(max_length=50, db_index=True)),
                ('title', models.CharField(max_length=50, null=True, blank=True)),
                ('description', models.CharField(max_length=500, blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('definition', djorm_pgjson.fields.JSONField(default={}, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('archived', models.DateTimeField(null=True, blank=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'recipe_type',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='recipetype',
            unique_together=set([('name', 'version')]),
        ),
        migrations.AddField(
            model_name='recipe',
            name='recipe_type',
            field=models.ForeignKey(to='recipe.RecipeType', on_delete=django.db.models.deletion.PROTECT),
            preserve_default=True,
        ),
    ]
