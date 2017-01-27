# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import connection, models, migrations


def copy_product_file(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute('SELECT * INTO product_file_temp FROM product_file')


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0004_auto_20170127_1324'),
    ]

    operations = [
        migrations.RunPython(copy_product_file),
    ]
