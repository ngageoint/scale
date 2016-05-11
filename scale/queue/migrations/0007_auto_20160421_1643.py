# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgjson.fields
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0016_auto_20160421_1553'),
        ('queue', '0006_auto_20160316_1625'),
    ]

    operations = [
        migrations.AddField(
            model_name='queue',
            name='configuration',
            field=djorm_pgjson.fields.JSONField(default={}, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='queue',
            name='job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, default=1, to='job.Job'),
            preserve_default=False,
        ),
    ]
