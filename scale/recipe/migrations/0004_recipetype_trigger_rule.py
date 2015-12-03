# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trigger', '0001_initial'),
        ('recipe', '0003_recipe_recipe_type_rev'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipetype',
            name='trigger_rule',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='trigger.TriggerRule', null=True),
            preserve_default=True,
        ),
    ]
