# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2018-12-20 20:14
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scheduler', '0012_remove_scheduler_resource_level'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scheduler',
            name='master_hostname',
        ),
        migrations.RemoveField(
            model_name='scheduler',
            name='master_port',
        ),
    ]