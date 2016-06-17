# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0009_auto_20160511_2204'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='is_superseded',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='recipe',
            name='root_superseded_recipe',
            field=models.ForeignKey(related_name='superseded_by_recipes', on_delete=django.db.models.deletion.PROTECT, blank=True, to='recipe.Recipe', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='recipe',
            name='superseded',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='recipe',
            name='superseded_recipe',
            field=models.OneToOneField(related_name='superseded_by_recipe', null=True, on_delete=django.db.models.deletion.PROTECT, blank=True, to='recipe.Recipe'),
            preserve_default=True,
        ),
    ]
