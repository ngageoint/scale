# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0003_auto_20170127_1319'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fileancestrylink',
            name='descendant',
            field=models.ForeignKey(related_name='ancestors', on_delete=django.db.models.deletion.PROTECT, blank=True, to='storage.ScaleFile', null=True),
            preserve_default=True,
        ),
    ]
