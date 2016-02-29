# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('queue', '0003_auto_20151023_1104'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='queue',
            name='is_job_type_paused',
        ),
    ]
