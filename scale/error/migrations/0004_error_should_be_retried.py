# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('error', '0003_error_is_builtin'),
    ]

    operations = [
        migrations.AddField(
            model_name='error',
            name='should_be_retried',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
