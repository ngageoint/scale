# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import connection, models, migrations
import django.db.models.deletion


def delete_constraint(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute('ALTER TABLE "file_ancestry_link" DROP CONSTRAINT "file_ancestry_li_descendant_id_34f8ed2a_fk_product_file_file_id"')


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0002_auto_20160622_1344'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fileancestrylink',
            name='descendant',
            field=models.ForeignKey(related_name='ancestors', on_delete=django.db.models.deletion.PROTECT, db_constraint=False, blank=True, to='product.ProductFile', null=True),
            preserve_default=True,
        ),
        migrations.RunPython(delete_constraint),
    ]
