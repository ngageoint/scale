# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0012_auto_20160330_1659'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recipejobold',
            name='job',
        ),
        migrations.RemoveField(
            model_name='recipejobold',
            name='recipe',
        ),
        migrations.DeleteModel(
            name='recipejobold',
        ),
    ]
