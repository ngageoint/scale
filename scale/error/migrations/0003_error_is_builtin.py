# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('error', '0002_auto_20151217_1319'),
    ]

    operations = [
        migrations.AddField(
            model_name='error',
            name='is_builtin',
            field=models.BooleanField(default=False, db_index=True),
            preserve_default=True,
        ),
    ]
