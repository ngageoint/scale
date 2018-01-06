from __future__ import unicode_literals

import django
from django.test import TransactionTestCase

from job.messages.process_job_inputs import ProcessJobInputs
from job.models import Job, JobInputFile
from job.test import utils as job_test_utils
from storage.test import utils as storage_test_utils


class TestProcessJobInputs(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting a ProcessJobInputs message to and from JSON"""

        job_1 = job_test_utils.create_job(num_exes=0, status='PENDING', input_file_size=None)
        job_2 = job_test_utils.create_job(num_exes=0, status='PENDING', input_file_size=None)
        job_ids = [job_1.id, job_2.id]

        # Add jobs to message
        message = ProcessJobInputs()
        if message.can_fit_more():
            message.add_job(job_1.id)
        if message.can_fit_more():
            message.add_job(job_2.id)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = ProcessJobInputs.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        self.assertEqual(len(new_message.new_messages), 1)
        self.assertEqual(new_message.new_messages[0].type, 'queued_jobs')
        # Jobs should have input_file_size set to 0 (no input files)
        self.assertEqual(jobs[0].disk_in_required, 0.0)
        self.assertEqual(jobs[1].disk_in_required, 0.0)

    def test_execute(self):
        """Tests calling ProcessJobInputs.execute() successfully"""

        workspace = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(workspace=workspace, file_size=10485760.0)
        file_2 = storage_test_utils.create_file(workspace=workspace, file_size=104857600.0)
        file_3 = storage_test_utils.create_file(workspace=workspace, file_size=987654321.0)
        interface = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }, {
                'name': 'Input 2',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'output_data': [{
                'name': 'Output 1',
                'type': 'files',
                'media_type': 'image/png',
            }]}
        job_type = job_test_utils.create_job_type(interface=interface)

        data_1 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Input 1',
                'file_id': file_1.id
            }, {
                'name': 'Input 2',
                'file_id': file_2.id
            }],
            'output_data': [{
                'name': 'Output 1',
                'workspace_id': workspace.id
            }]}
        data_2 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Input 1',
                'file_id': file_2.id
            }, {
                'name': 'Input 2',
                'file_id': file_3.id
            }],
            'output_data': [{
                'name': 'Output 1',
                'workspace_id': workspace.id
            }]}

        job_1 = job_test_utils.create_job(job_type=job_type, num_exes=0, status='PENDING', input_file_size=None,
                                          input=data_1)
        job_2 = job_test_utils.create_job(job_type=job_type, num_exes=0, status='PENDING', input_file_size=None,
                                          input=data_2)
        job_ids = [job_1.id, job_2.id]

        # Add jobs to message
        message = ProcessJobInputs()
        if message.can_fit_more():
            message.add_job(job_1.id)
        if message.can_fit_more():
            message.add_job(job_2.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        # Check for queued jobs message
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'queued_jobs')

        # Check jobs for expected input_file_size
        self.assertEqual(jobs[0].disk_in_required, 110.0)
        self.assertEqual(jobs[1].disk_in_required, 1042.0)

        # Make sure job input file models are created
        job_input_files = JobInputFile.objects.filter(job_id=job_1.id)
        self.assertEqual(len(job_input_files), 2)
        for job_input_file in job_input_files:
            if job_input_file.job_input == 'Input 1':
                self.assertEqual(job_input_file.input_file_id, file_1.id)
            elif job_input_file.job_input == 'Input 2':
                self.assertEqual(job_input_file.input_file_id, file_2.id)
            else:
                self.fail('Invalid input name: %s' % job_input_file.job_input)
        job_input_files = JobInputFile.objects.filter(job_id=job_2.id)
        self.assertEqual(len(job_input_files), 2)
        for job_input_file in job_input_files:
            if job_input_file.job_input == 'Input 1':
                self.assertEqual(job_input_file.input_file_id, file_2.id)
            elif job_input_file.job_input == 'Input 2':
                self.assertEqual(job_input_file.input_file_id, file_3.id)
            else:
                self.fail('Invalid input name: %s' % job_input_file.job_input)

        # Test executing message again
        message_json_dict = message.to_json()
        message = ProcessJobInputs.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        # Still should have queued jobs message
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'queued_jobs')

        # Make sure job input file models are unchanged
        job_input_files = JobInputFile.objects.filter(job_id=job_1.id)
        self.assertEqual(len(job_input_files), 2)
        job_input_files = JobInputFile.objects.filter(job_id=job_2.id)
        self.assertEqual(len(job_input_files), 2)
