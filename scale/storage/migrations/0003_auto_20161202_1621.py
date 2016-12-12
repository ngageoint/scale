# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0002_workspace_is_move_enabled'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scalefile',
            name='data_ended',
            field=models.DateTimeField(db_index=True, null=True, blank=True),
            preserve_default=True,
        ),
    ]
