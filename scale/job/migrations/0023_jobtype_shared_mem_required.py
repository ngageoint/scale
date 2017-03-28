# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0022_jobtype_configuration'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobtype',
            name='shared_mem_required',
            field=models.FloatField(default=0.0),
            preserve_default=True,
        ),
    ]
