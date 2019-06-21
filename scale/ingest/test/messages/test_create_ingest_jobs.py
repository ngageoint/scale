from __future__ import unicode_literals

import django
from django.test import TestCase
from django.utils.timezone import now

import job.test.utils as job_test_utils
import ingest.test.utils as ingest_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils

from ingest.messages.create_ingest_jobs import create_strike_ingest_job_message
from ingest.models import Strike
from ingest.strike.configuration.json.configuration_v6 import StrikeConfigurationV6
from messaging.backends.amqp import AMQPMessagingBackend
from messaging.backends.factory import add_message_backend
from storage.models import ScaleFile


class TestCreateIngest(TestCase):
    
    fixtures = ['ingest_job_types']
    
    def setUp(self):
        django.setup()
        add_message_backend(AMQPMessagingBackend)
        
        manifest = job_test_utils.create_seed_manifest(inputs_files=[{'name': 'INPUT_FILE', 'media_types': ['text/plain'], 'required': True, 'multiple': True}], inputs_json=[])
        self.jt1 = job_test_utils.create_seed_job_type(manifest=manifest)
        recipe_type_def = {'version': '6',
                           'input': {'files': [{'name': 'INPUT_FILE',
                                                'media_types': ['text/plain'],
                                                'required': True,
                                                'multiple': True}],
                                    'json': []},
                           'nodes': {'node_a': {'dependencies': [],
                                                'input': {'INPUT_FILE': {'type': 'recipe', 'input': 'INPUT_FILE'}},
                                                'node_type': {'node_type': 'job', 'job_type_name': self.jt1.name,
                                                              'job_type_version': self.jt1.version,
                                                              'job_type_revision': 1}}}}

        self.recipe = recipe_test_utils.create_recipe_type_v6(name='test-recipe', definition=recipe_type_def)
        
    def test_json_create(self):
        """Tests converting a CreateIngest message to and from json
        """
        
        workspace_1 = storage_test_utils.create_workspace()
        workspace_2 = storage_test_utils.create_workspace()
        source_file = ScaleFile.objects.create(file_name='input_file', file_type='SOURCE',
                                               media_type='text/plain', file_size=10, data_type_tags=['type1'],
                                                file_path='the_path', workspace=workspace_1)
        source_file.add_data_type_tag('type1')
        source_file.add_data_type_tag('type2')
        source_file.add_data_type_tag('type3')
        
        ingest = ingest_test_utils.create_ingest(source_file=source_file, new_workspace=workspace_2)
        
        strike_config = {
            'version': '6',
            'workspace': workspace_1.name,
            'monitor': {'type': 'dir-watcher', 'transfer_suffix': '_tmp'},
            'files_to_ingest': [{
                'filename_regex': 'input_file',
                'data_types': ['image_type'],
                'new_workspace': workspace_2.name,
                'new_file_path': 'my/path'
            }],
            'recipe': {
                'name': self.recipe.name
            },
        }
        config = StrikeConfigurationV6(strike_config).get_configuration()
        strike = Strike.objects.create_strike('my_name', 'my_title', 'my_description', config)
        
        message = create_strike_ingest_job_message(ingest.id, ingest.workspace.name, ingest.new_workspace.name, strike.id)
        message.execute()
        import pdb; pdb.set_trace()
        pass
        