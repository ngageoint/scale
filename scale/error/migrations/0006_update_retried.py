from __future__ import unicode_literals

from django.db import migrations



class Migration(migrations.Migration):

    dependencies = [
        ('error', '0005_auto_20180621_2110'),
    ]

    def update_should_be_retried(apps, schema_editor):
        # Go through all of the Error models and update which ones should be automatically retried according to #1611
        Error = apps.get_model('error', 'Error')
        names = ['pull-timeout', 'pre-timeout', 'post-timeout', 'system-timeout', 'ingest-timeout', 'pull',
                 'unknown', 'database', 'nfs', 'mesos-lost']

        for error in Error.objects.all().iterator():
            if error.name in names:
                error.should_be_retried = True
                error.save()

    operations = [
        migrations.RunPython(update_should_be_retried),
    ]
