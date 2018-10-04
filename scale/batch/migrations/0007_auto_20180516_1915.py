# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-05-16 19:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('batch', '0006_auto_20180401_0218'),
    ]

    operations = [
        migrations.AlterField(
            model_name='batchmetrics',
            name='batch',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='metrics', to='batch.Batch'),
        ),
    ]