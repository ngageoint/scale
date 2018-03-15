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
            self.results_dict = {'version': '2.0', 'output_data': []}
        self.output_data = self.results_dict['output_data']

    def add_file_list_parameter(self, name, file_ids):
        """Adds a list of files to the job results

        :param name: The output parameter name
        :type name: string
        :param file_ids: The file IDs
        :type file_ids: [long]
        """

        self.output_data.append({'name': name, 'file_ids': file_ids})

    def add_file_parameter(self, name, file_id):
        """Adds a file to the job results

        :param name: The output parameter name
        :type name: string
        :param file_id: The file ID
        :type file_id: long
        """

        self.output_data.append({'name': name, 'file_id': file_id})

    def add_output_to_data(self, output_name, job_data, input_name):
        """Adds the given output from the results as a new input in the given job data

        :param output_name: The name of the results output to add to the data
        :type output_name: string
        :param job_data: The job data
        :type job_data: :class:`job.configuration.data.job_data.JobData`
        :param input_name: The name of the data input
        :type input_name: string
        """

        for output_data in self.output_data:
            if output_name == output_data['name']:
                if 'file_id' in output_data:
                    file_id = output_data['file_id']
                    job_data.add_file_input(input_name, file_id)
                elif 'file_ids' in output_data:
                    file_ids = output_data['file_ids']
                    job_data.add_file_list_input(input_name, file_ids)
                break

    def add_output_json(self, output_name, value):
        """Adds the given output json from the seed.outputs.json file

        :param output_name: Output JSON key used to capture from output file
        :type output_name: str
        :param value: Raw value provided by job
        :type value: float or str or dict or array
        """

        self.output_data.append({'name': output_name, 'json': value})

    def get_dict(self):
        """Returns the internal dictionary that represents these job results

        :returns: The dictionary representing the results
        :rtype: dict
        """

        return self.results_dict

    def extend_interface_with_outputs(self, interface, job_files):
        """Add a value property to both files and json objects within Seed Manifest

        :param interface: Seed manifest which should have concrete outputs injected
        :type interface: :class:`job.seed.manifest.SeedManifest`
        :param job_files: A list of files that are referenced by the job data.
        :type job_files: [:class:`storage.models.ScaleFile`]
        :return: A dictionary of Seed Manifest outputs key mapped to the corresponding data value.
        :rtype: dict
        """

        files = []
        json = []
        file_map = {job_file.id: job_file for job_file in job_files}
        outputs = interface.get_outputs()
        for i in interface.get_output_files():
            for j in self.output_data:
                if i['name'] is j['name']:
                    i['value'] = [file_map[str(x)] for x in j.file_ids]
                    break
            files.append(i)

        for i in interface.get_output_json():
            for j in self.output_data:
                if i['name'] is j['name']:
                    i['value'] = j['json']
                    break
            json.append(i)

        outputs['files'] = files
        outputs['json'] = json
        return outputs