"""Defines the results obtained after executing a job"""
from __future__ import unicode_literals


class JobResults(object):
    """Represents the results obtained after executing a job
    """

    def __init__(self, results_dict=None):
        """Constructor

        :param results_dict: The dictionary representing the job results
        :type results_dict: dict
        """

        if results_dict:
            self.results_dict = results_dict
        else:
            self.results_dict = {u'version': u'1.0', u'output_data': []}
        self.output_data = self.results_dict[u'output_data']

    def add_file_list_parameter(self, name, file_ids):
        """Adds a list of files to the job results

        :param name: The output parameter name
        :type name: str
        :param file_ids: The file IDs
        :type file_ids: list of long
        """

        self.output_data.append({u'name': name, u'file_ids': file_ids})

    def add_file_parameter(self, name, file_id):
        """Adds a file to the job results

        :param name: The output parameter name
        :type name: str
        :param file_id: The file ID
        :type file_id: long
        """

        self.output_data.append({u'name': name, u'file_id': file_id})

    def add_output_to_data(self, output_name, job_data, input_name):
        """Adds the given output from the results as a new input in the given job data

        :param output_name: The name of the results output to add to the data
        :type output_name: str
        :param job_data: The job data
        :type job_data: :class:`job.configuration.data.job_data.JobData`
        :param input_name: The name of the data input
        :type input_name: str
        """

        for output_data in self.output_data:
            if output_name == output_data[u'name']:
                if u'file_id' in output_data:
                    file_id = output_data[u'file_id']
                    job_data.add_file_input(input_name, file_id)
                elif u'file_ids' in output_data:
                    file_ids = output_data[u'file_ids']
                    job_data.add_file_list_input(input_name, file_ids)
                break

    def get_dict(self):
        """Returns the internal dictionary that represents these job results

        :returns: The dictionary representing the results
        :rtype: dict
        """

        return self.results_dict
