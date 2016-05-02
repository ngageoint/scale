# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0003_auto_20160201_0846'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduler',
            name='docker_repository',
            field=models.CharField(default='geoint', max_length=250),
            preserve_default=True,
        ),
    ]
