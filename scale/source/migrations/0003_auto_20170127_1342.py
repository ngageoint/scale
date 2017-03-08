# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0004_auto_20170127_1324'),
        ('storage', '0003_auto_20161202_1621'),
        ('recipe', '0016_recipefile_data'),
        ('ingest', '0008_auto_20170127_1332'),
        ('source', '0002_auto_20170127_1336'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sourcefile',
            name='file',
        ),
        migrations.DeleteModel(
            name='SourceFile',
        ),
        migrations.CreateModel(
            name='SourceFile',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('storage.scalefile',),
        ),
    ]
