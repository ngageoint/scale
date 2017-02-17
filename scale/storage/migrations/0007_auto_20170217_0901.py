# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0006_auto_20170127_1423'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scalefile',
            name='file_type',
            field=models.CharField(default='SOURCE', max_length=50, choices=[('SOURCE', 'SOURCE'), ('PRODUCT', 'PRODUCT')]),
            preserve_default=True,
        ),
        migrations.AlterIndexTogether(
            name='scalefile',
            index_together=set([('file_type', 'last_modified'), ('file_type', 'data_started', 'data_ended')]),
        ),
    ]
