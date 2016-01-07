# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('error', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='error',
            name='description',
            field=models.CharField(max_length=250, null=True),
            preserve_default=True,
        ),
    ]
