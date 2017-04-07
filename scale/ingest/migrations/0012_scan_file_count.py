# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0011_auto_20170302_2130'),
    ]

    operations = [
        migrations.AddField(
            model_name='scan',
            name='file_count',
            field=models.BigIntegerField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
