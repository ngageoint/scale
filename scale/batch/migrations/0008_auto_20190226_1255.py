# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-02-26 12:55
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('batch', '0007_auto_20180516_1915'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='batch',
            name='completed_job_count',
        ),
        migrations.RemoveField(
            model_name='batch',
            name='completed_recipe_count',
        ),
        migrations.RemoveField(
            model_name='batch',
            name='created_count',
        ),
        migrations.RemoveField(
            model_name='batch',
            name='failed_count',
        ),
        migrations.RemoveField(
            model_name='batch',
            name='status',
        ),
        migrations.RemoveField(
            model_name='batch',
            name='total_count',
        ),
    ]
