# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0009_jobtype_revision_num'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobtype',
            name='max_tries',
            field=models.IntegerField(default=3),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='jobtype',
            name='priority',
            field=models.IntegerField(default=100),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='jobtype',
            name='timeout',
            field=models.IntegerField(default=1800),
            preserve_default=True,
        ),
    ]
