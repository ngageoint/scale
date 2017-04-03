# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0004_auto_20170209_1616'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduler',
            name='queue_mode',
            field=models.CharField(default='FIFO', max_length=50, choices=[('FIFO', 'FIFO'), ('LIFO', 'LIFO')]),
            preserve_default=True,
        ),
    ]
