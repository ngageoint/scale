# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trigger', '0003_auto_20151202_1325'),
    ]

    operations = [
        migrations.AlterField(
            model_name='triggerrule',
            name='name',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=False,
        ),
    ]
