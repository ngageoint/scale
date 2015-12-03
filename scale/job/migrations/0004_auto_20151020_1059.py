# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0003_auto_20151016_0849'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='status',
            field=models.CharField(default='PENDING', max_length=50, db_index=True, choices=[('PENDING', 'PENDING'), ('BLOCKED', 'BLOCKED'), ('QUEUED', 'QUEUED'), ('RUNNING', 'RUNNING'), ('FAILED', 'FAILED'), ('COMPLETED', 'COMPLETED'), ('CANCELED', 'CANCELED')]),
            preserve_default=True,
        ),
    ]
