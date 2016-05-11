# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('queue', '0007_auto_20160421_1643'),
    ]

    def update_queue_models(apps, schema_editor):
        # Go through all of the queue models and update their new job and configuration fields
        Queue = apps.get_model('queue', 'Queue')
        total_count = Queue.objects.all().count()
        print 'Updating %s queue models' % str(total_count)
        done_count = 0
        for queue in Queue.objects.select_related('job_exe__job').iterator():
            if done_count % 1000 == 0:
                percent = (done_count / total_count) * 100.00
                print 'Completed %s of %s queue models (%f%%)' % (done_count, total_count, percent)
            done_count += 1

            queue.job_id = queue.job_exe.job_id
            queue.configuration = queue.job_exe.job.configuration
            queue.save()
        print 'All %s queue models completed' % str(total_count)

    operations = [
        migrations.RunPython(update_queue_models),
    ]
