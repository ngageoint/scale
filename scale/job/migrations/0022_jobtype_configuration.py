# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgjson.fields


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0021_auto_20161115_1524'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobtype',
            name='configuration',
            field=djorm_pgjson.fields.JSONField(default={}, null=True, blank=True),
            preserve_default=True,
        ),
    ]
