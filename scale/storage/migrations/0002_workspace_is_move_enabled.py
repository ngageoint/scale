# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='workspace',
            name='is_move_enabled',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
