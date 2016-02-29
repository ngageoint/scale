# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0010_auto_20151208_1503'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobtype',
            name='max_scheduled',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
