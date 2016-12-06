# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ingest', '0006_auto_20161202_1621'),
        ('source', '0001_initial'),
    ]

    def populate_ingest_data_time(apps, schema_editor):
        # Go through all of the parsed source file models and populate data time for ingest models
        SourceFile = apps.get_model('source', 'SourceFile')
        Ingest = apps.get_model('ingest', 'Ingest')

        total_count = SourceFile.objects.filter(is_parsed=True).count()
        if not total_count:
            return

        print('\nUpdating ingests for source files: %i' % total_count)
        done_count = 0
        batch_size = 500
        while done_count < total_count:
            batch_end = done_count + batch_size

            for src_file in SourceFile.objects.filter(is_parsed=True).order_by('id')[done_count:batch_end]:
                Ingest.objects.filter(source_file_id=src_file.id).update(data_started=src_file.data_started,
                                                                         data_ended=src_file.data_ended)
                done_count += 1

            percent = (float(done_count) / float(total_count)) * 100.00
            print('Progress: %i/%i (%.2f%%)' % (done_count, total_count, percent))
        print ('Migration finished.')

    operations = [
        migrations.RunPython(populate_ingest_data_time),
    ]
