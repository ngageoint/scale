# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0003_auto_20161202_1621'),
        ('recipe', '0016_recipefile_data'),
        ('ingest', '0008_auto_20170127_1332'),
        ('product', '0005_auto_20170127_1344'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productfile',
            name='file',
        ),
        migrations.RemoveField(
            model_name='productfile',
            name='job',
        ),
        migrations.RemoveField(
            model_name='productfile',
            name='job_exe',
        ),
        migrations.RemoveField(
            model_name='productfile',
            name='job_type',
        ),
        migrations.DeleteModel(
            name='ProductFile',
        ),
        migrations.CreateModel(
            name='ProductFile',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('storage.scalefile',),
        ),
    ]
