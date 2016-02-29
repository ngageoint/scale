# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('node', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='node',
            name='pause_reason',
            field=models.CharField(max_length=250, null=True),
            preserve_default=True,
        ),
    ]
