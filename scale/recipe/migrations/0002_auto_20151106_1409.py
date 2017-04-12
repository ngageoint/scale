# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import util.deprecation
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecipeTypeRevision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('revision_num', models.IntegerField()),
                ('definition', util.deprecation.JSONStringField(default={}, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('recipe_type', models.ForeignKey(to='recipe.RecipeType', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'db_table': 'recipe_type_revision',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='recipetyperevision',
            unique_together=set([('recipe_type', 'revision_num')]),
        ),
    ]
