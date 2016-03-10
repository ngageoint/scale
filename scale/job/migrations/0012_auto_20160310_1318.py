# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0011_jobtype_max_scheduled'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='last_modified',
            field=models.DateTimeField(auto_now=True, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='jobexecution',
            name='last_modified',
            field=models.DateTimeField(auto_now=True, db_index=True),
            preserve_default=True,
        ),
    ]
