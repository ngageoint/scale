# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import util.deprecation


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0021_auto_20161115_1524'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobtype',
            name='configuration',
            field=util.deprecation.JSONStringField(default={}, null=True, blank=True),
            preserve_default=True,
        ),
    ]
