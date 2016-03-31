# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0009_auto_20160330_1412'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='recipejob',
            new_name='recipejobold',
        ),
        migrations.AlterModelTable(
            name='recipejobold',
            table='recipe_job_old',
        ),
    ]
