# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('batch', '0001_initial'),
        ('product', '0006_auto_20170127_1348'),
    ]

    operations = [
        migrations.AddField(
            model_name='fileancestrylink',
            name='batch',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='batch.Batch', null=True),
            preserve_default=True,
        ),
    ]
