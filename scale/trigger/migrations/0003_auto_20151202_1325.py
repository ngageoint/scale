# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trigger', '0002_auto_20151125_1438'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='triggerrule',
            name='description',
        ),
        migrations.RemoveField(
            model_name='triggerrule',
            name='title',
        ),
        migrations.AlterField(
            model_name='triggerrule',
            name='name',
            field=models.CharField(max_length=50, null=True, blank=True),
            preserve_default=True,
        ),
    ]
