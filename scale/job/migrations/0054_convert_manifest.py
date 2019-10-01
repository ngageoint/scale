# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-03-12 11:53
from __future__ import unicode_literals

from django.db import migrations

from job.deprecation import JobInterfaceSunset
from job.seed.manifest import SeedManifest

INTERFACE_NAME_COUNTER = 0

def get_unique_name(name):
    global INTERFACE_NAME_COUNTER
    new_name = '%s_%d' % (name, INTERFACE_NAME_COUNTER)
    new_name = new_name.replace(' ', '_')
    INTERFACE_NAME_COUNTER += 1
    return new_name

def convert_interface_to_manifest(apps, schema_editor):
    # Go through all of the JobType models and convert legacy interfaces to Seed manifests
    # Also inactivate/pause them
    JobType = apps.get_model('job', 'JobType')
    JobTypeRevision = apps.get_model('job', 'JobTypeRevision')
    RecipeTypeJobLink = apps.get_model('recipe', 'RecipeTypeJobLink')
    RecipeType = apps.get_model('recipe', 'RecipeType')

    unique = 0
    for jt in JobType.objects.all().iterator():
        if JobInterfaceSunset.is_seed_dict(jt.manifest):
            continue
        jt.is_active = False
        jt.is_paused = True
        old_name = jt.name
        old_name_version = jt.name + ' ' + jt.version
        jt.name = 'legacy-' + jt.name.replace('_', '-')
        jt.name = jt.name.replace(' ', '-')
            
        if not jt.manifest:
            jt.manifest = {}
            
        input_files = []
        input_json = []
        output_files = []
        global INTERFACE_NAME_COUNTER
        INTERFACE_NAME_COUNTER = 0
        for input in jt.manifest.get('input_data', []):
            type = input.get('type', '')
            if 'file' not in type:
                json = {}
                json['name'] = get_unique_name(input.get('name'))
                json['type'] = 'string'
                json['required'] = input.get('required', True)
                input_json.append(json)
                continue
            file = {}
            file['name'] = get_unique_name(input.get('name'))
            file['required'] = input.get('required', True)
            file['partial'] = input.get('partial', False)
            file['mediaTypes'] = input.get('media_types', [])
            file['multiple'] = (type == 'files')
            input_files.append(file)
            
        for output in jt.manifest.get('output_data', []):
            type = output.get('type', '')
            file = {}
            file['name'] = get_unique_name(output.get('name'))
            file['required'] = output.get('required', True)
            file['mediaType'] = output.get('media_type', '')
            file['multiple'] = (type == 'files')
            file['pattern'] = "*.*"
            output_files.append(file)
            
        mounts = []
        for mount in jt.manifest.get('mounts', []):
            mt = {}
            mt['name'] = get_unique_name(mount.get('name'))
            mt['path'] = mount.get('path')
            mt['mode'] = mount.get('mode', 'ro')
            mounts.append(mt)
            
        settings = []
        for setting in jt.manifest.get('settings', []):
            s = {}
            s['name'] = get_unique_name(setting.get('name'))
            s['secret'] = setting.get('secret', False)
            settings.append(s)
        for var in jt.manifest.get('env_vars', []):
            s = {}
            name = get_unique_name(var.get('name'))
            name = 'ENV_' + name
            s['name'] = name
            settings.append(s)
        
        errors = []
        if jt.error_mapping:
            ec = jt.error_mapping.get('exit_codes', {})
            for exit_code, error_name in ec.items():
                error = {
                    'code': int(exit_code),
                    'name': get_unique_name(error_name),
                    'title': 'Error Name',
                    'description': 'Error Description',
                    'category': 'algorithm'
                }
                errors.append(error)
            
        author_name = jt.author_name if jt.author_name else 'unknown'
        author_url = jt.author_url if jt.author_url else 'unknown'
        description = jt.description if jt.description else 'none'
        category = jt.category if jt.category else 'no-category'
        timeout = jt.timeout if jt.timeout else 999
        cpu = jt.cpus_required if jt.cpus_required else 1.0 
        mem = jt.mem_const_required if jt.mem_const_required else 64.0 
        sharedMem = jt.shared_mem_required if jt.shared_mem_required else 0.0
        mem_mult = jt.mem_mult_required if jt.mem_mult_required else 0.0 
        disk = jt.disk_out_const_required if jt.disk_out_const_required else 64.0 
        disk_mult = jt.disk_out_mult_required if jt.disk_out_mult_required else 0.0 
        new_manifest = {
            'seedVersion': '1.0.0',
            'job': {
                'name': jt.name,
                'jobVersion': '0.0.0',
                'packageVersion': '1.0.0',
                'title': 'LEGACY ' + jt.title,
                'description': jt.description,
                'tags': [category, old_name_version],
                'maintainer': {
                  'name': author_name,
                  'email': 'jdoe@example.com',
                  'url': author_url
                },
                'timeout': timeout,
                'interface': {
                  'command': jt.manifest.get('command', ''),
                  'inputs': {
                    'files': input_files,
                    'json': input_json
                  },
                  'outputs': {
                    'files': output_files,
                    'json': []
                  },
                  'mounts': mounts,
                  'settings': settings
                },
                'resources': {
                  'scalar': [
                    { 'name': 'cpus', 'value': cpu },
                    { 'name': 'mem', 'value': mem, 'inputMultiplier': mem_mult },
                    { 'name': 'sharedMem', 'value': sharedMem },
                    { 'name': 'disk', 'value': disk, 'inputMultiplier': disk_mult }
                  ]
                },
                'errors': errors
              }
            }
        jt.manifest = new_manifest
        SeedManifest(jt.manifest, do_validate=True)
        jt.save()
        for jtr in JobTypeRevision.objects.filter(job_type_id=jt.id).iterator():
            jtr.manifest = jt.manifest
            jtr.save()
            
        
        # Update any recipe types that reference the updated job name
        for rtjl in RecipeTypeJobLink.objects.all().filter(job_type_id=jt.id).iterator():
            definition = rtjl.recipe_type.definition
            changed = False

            # v6 
            if 'nodes' in definition:
                for name, node in definition['nodes'].items():
                    nt = node['node_type']
                    if nt['node_type'] == 'job' and nt['job_type_name'] == old_name and nt['job_type_version'] == jt.version:
                        nt['job_type_name'] = jt.name
                        changed = True
            # v5
            elif 'jobs' in definition:
                for job in definition['jobs']:
                    jt_node = job['job_type']
                    if jt_node['name'] == old_name and jt_node['version'] == jt.version:
                        job['job_type']['name'] = jt.name
                        changed = True

            if changed:
                rtjl.recipe_type.definition = definition
                rtjl.recipe_type.save()

class Migration(migrations.Migration):

    dependencies = [
        ('job', '0053_jobtype_unmet_resources'),
        ('recipe', '0037_remove_recipetype_trigger_rule')
    ]

    operations = [
        migrations.RunPython(convert_interface_to_manifest),
    ]
