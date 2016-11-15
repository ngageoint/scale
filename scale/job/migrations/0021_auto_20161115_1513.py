# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0020_auto_20161110_1517'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taskupdate',
            name='task_id',
            field=models.CharField(max_length=250),
            preserve_default=True,
        ),
    ]
