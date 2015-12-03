# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0002_auto_20151106_1409'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='recipe_type_rev',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, default=1, to='recipe.RecipeTypeRevision'),
            preserve_default=False,
        ),
    ]
