# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='productfile',
            name='is_superseded',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='productfile',
            name='superseded',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
