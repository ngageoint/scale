# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0006_auto_20151125_1404'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='last_modified',
            field=models.DateTimeField(auto_now=True, db_index=True),
            preserve_default=True,
        ),
    ]
