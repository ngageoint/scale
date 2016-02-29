#@PydevCodeAnalysisIgnore

import django
from django.test import TestCase
from mock import MagicMock, patch

from job.configuration.results.job_results import JobResults


class TestJobResultsAddOutputToData(TestCase):

    def setUp(self):
        django.setup()

    def test_successful_file(self):
        '''Tests calling JobResults.add_output_to_data() successfully with a file parameter'''

        output_name = u'foo'
        file_id = 1337
        input_name = u'bar'

        results = JobResults()
        results.add_file_parameter(output_name, file_id)

        job_data = MagicMock()
        results.add_output_to_data(output_name, job_data, input_name)
        job_data.add_file_input.assert_called_with(input_name, file_id)

    def test_successful_file_list(self):
        '''Tests calling JobResults.add_output_to_data() successfully with a file list parameter'''

        output_name = u'foo'
        file_ids = [1, 2, 3, 4]
        input_name = u'bar'

        results = JobResults()
        results.add_file_list_parameter(output_name, file_ids)

        job_data = MagicMock()
        results.add_output_to_data(output_name, job_data, input_name)
        job_data.add_file_list_input.assert_called_with(input_name, file_ids)
