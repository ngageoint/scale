# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0002_workspace_is_move_enabled'),
        ('recipe', '0014_auto_20160608_1402'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecipeFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('recipe', models.ForeignKey(to='recipe.Recipe', on_delete=django.db.models.deletion.PROTECT)),
                ('scale_file', models.ForeignKey(to='storage.ScaleFile', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'db_table': 'recipe_file',
            },
            bases=(models.Model,),
        ),
    ]
