# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0017_auto_20160426_1556'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='jobexecution',
            name='current_stderr_url',
        ),
        migrations.RemoveField(
            model_name='jobexecution',
            name='current_stdout_url',
        ),
    ]
