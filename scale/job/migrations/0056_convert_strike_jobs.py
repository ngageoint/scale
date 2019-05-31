from __future__ import unicode_literals

from django.db import migrations

def convert_strike_job_inputs(apps, schema_editor):
    Strike = apps.get_model('ingest', 'Strike')
    Job = apps.get_model('job', 'Job')
    
    strikes = Strike.objects.all().iterator()
    for strike in strikes:
        strike_job = Job.objects.get(pk=strike.job_id)

        changed = False
        if strike_job.input['version'] == '6':
            if 'Strike ID' in strike_job.input['json']:
                strike_job.input['json']['STRIKE_ID'] = strike_job.input['json']['Strike ID']
                del strike_job.input['json']['Strike ID']
                changed = True
        else:
            for i_data in strike_job.input['input_data']:
                if i_data['name'] == 'Strike ID':
                    i_data['name'] = 'STRIKE_ID'
                    changed = True

        if changed:
            strike_job.save()

class Migration(migrations.Migration):

    dependencies = [
        ('job', '0055_jobtype_v5_deprecation'),
    ]

    operations = [
       migrations.RunPython(convert_strike_job_inputs),
    ]
