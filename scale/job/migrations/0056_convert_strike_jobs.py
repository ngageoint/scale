from __future__ import unicode_literals

from django.db import migrations

def convert_strike_job_inputs(apps, schema_editor):
    """Converts any strike job inputs to contain the new 'STRIKE_ID' key instead
    of 'Strike ID'
    """
    
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
            
def convert_scan_job_inputs(apps, schema_editor):
    """Converts any pending/queued/blocked/running scan job inputs to contain the 
    new 'SCAN_ID' key instead of 'Scan ID'
    """
    
    Scan = apps.get_model('ingest', 'scan')
    Job = apps.get_model('job', 'Job')
    
    scans = Scan.objects.all().iterator()
    for scan in scans:
        scan_job = Job.objects.get(pk=scan.job_id)
        if scan_job.status in ['PENDING', 'QUEUED', 'BLOCKED', 'RUNNING']:
            changed = False
            
            if scan_job.input['version'] == '6':
                if 'Scan ID' in scan_job.input['json']:
                    scan_job.input['json']['SCAN_ID'] = scan_job.input['json']['Scan ID']
                    del scan_job.input['json']['Scan ID']
                    changed = True
            else:
                for i_data in scan_job.input['input_data']:
                    if i_data['name'] == 'Scan ID':
                        i_data['name'] = 'SCAN_ID'
                        changed = True
    
            if changed:
                scan_job.save()

class Migration(migrations.Migration):

    dependencies = [
        ('job', '0055_jobtype_v5_deprecation'),
    ]

    operations = [
       migrations.RunPython(convert_strike_job_inputs),
       migrations.RunPython(convert_scan_job_inputs),
    ]
