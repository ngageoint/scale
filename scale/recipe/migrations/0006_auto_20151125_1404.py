# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0005_recipetype_revision_num'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipetype',
            name='title',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=False,
        ),
    ]
