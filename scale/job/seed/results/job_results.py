"""Defines the results obtained after executing a job"""
from __future__ import unicode_literals

import json
import logging

import os
from job.configuration.data.data_file import DATA_FILE_STORE
from job.seed.metadata import METADATA_SUFFIX, SeedMetadata
from job.seed.results.outputs_json import SeedOutputsJson
from job.seed.types import SeedOutputFiles
from product.types import ProductFileMetadata

logger = logging.getLogger(__name__)


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

    def perform_post_steps(self, job_interface, job_data, job_exe):
        """Stores the files or JSON output of job and deletes any working directories

        :param job_interface: The job interface
        :type job_interface: :class:`job.seed.manifest.SeedManifest`
        :param job_data: The job data
        :type job_data: :class:`job.data.job_data.JobData`
        :param job_exe: The job execution model with related job and job_type fields
        :type job_exe: :class:`job.models.JobExecution`
        :return: Job results generated by job execution
        :rtype: :class:`job.seed.results.job_results.JobResults`
        """

        # For compliance with Seed we must capture all files directly from the output directory.
        # The capture expressions can be found within `interface.outputs.files.pattern`

        output_files = self._capture_output_files(job_interface.get_seed_output_files())

        self._capture_output_json(job_interface.get_seed_output_json())

        self._store_output_data_files(output_files, job_data, job_exe)

    def _capture_output_files(self, seed_output_files):
        """Evaluate files patterns and capture any available side-car metadata associated with matched files

        :param seed_output_files: interface definition of Seed output files that should be captured
        :type seed_output_files: [`job.seed.types.SeedOutputFiles`]
        :return: collection of files name keys mapped to a ProductFileMetadata list. { name : [`ProductFileMetadata`]
        :rtype: dict
        """

        # Dict of detected files and associated metadata
        captured_files = {}

        # Iterate over each files object
        for output_file in seed_output_files:
            # For files obj that are detected, handle results (may be multiple)
            product_files = []
            for matched_file in output_file.get_files():

                product_file_meta = ProductFileMetadata(output_file.name, matched_file, output_file.media_type)

                # check to see if there is side-car metadata files
                metadata_file = os.path.join(matched_file, METADATA_SUFFIX)

                # If metadata is found, attempt to grab any Scale relevant data and place in ProductFileMetadata tuple
                if os.path.isfile(metadata_file):
                    with open(metadata_file) as metadata_file_handle:
                        metadata = SeedMetadata(json.load(metadata_file_handle))

                        # Create a GeoJSON object, as the present Seed Metadata schema only uses the Geometry fragment
                        # TODO: Update if Seed schema updates.  Ref: https://github.com/ngageoint/seed/issues/95
                        product_file_meta.geojson = \
                            {
                                'type': 'Feature',
                                'geometry': metadata.get_geometry()
                            }

                        timestamp = metadata.get_time()

                        # Seed Metadata Schema defines start / end as required
                        # so we do not need to check here.
                        if timestamp:
                            product_file_meta.data_start = timestamp['start']
                            product_file_meta.data_end = timestamp['end']

                product_files.append(product_file_meta)

            captured_files[output_file.name] = product_files

        return captured_files

    def _capture_output_json(self, output_json_interface):
        """Captures any JSON property output from a job execution

        :param outputs_json_interface: List of output json interface objects
        :type outputs_json_interface: [:class:`job.seed.types.SeedOutputJson`]
        """

        # Identify any outputs from seed.outputs.json
        try:
            schema = SeedOutputsJson.construct_schema(output_json_interface)
            outputs = SeedOutputsJson.read_outputs(schema)
            seed_outputs_json = outputs.get_values(output_json_interface)

            for key in seed_outputs_json:
                self.add_output_json(key, seed_outputs_json[key])
        except IOError:
            logger.warning('No seed.outputs.json file found to process.')

    def _store_output_data_files(self, data_files, job_data, job_exe):
        """Stores the given output data

        :param data_files: Dict with each file parameter name mapping to a ProductFileMetadata class
        :type data_files: {string: ProductFileMetadata)
        :param job_exe: The job execution model (with related job and job_type fields) that is storing the output data
            files
        :type job_exe: :class:`job.models.JobExecution`
        :returns: The job results
        :rtype: :class:`job.configuration.results.job_results.JobResults`
        """

        # Organize the data files
        workspace_files = {}  # Workspace ID -> [`ProductFileMetadata`]
        params_by_file_path = {}  # Absolute local file path -> output parameter name
        for name in data_files:
            file_output = job_data.get_output_file_by_id(name)
            workspace_id = file_output.workspace_id
            if workspace_id in workspace_files:
                workspace_file_list = workspace_files[workspace_id]
            else:
                workspace_file_list = []
                workspace_files[workspace_id] = workspace_file_list
            data_file_entry = data_files[name]
            for entry in data_file_entry:
                file_path = os.path.normpath(entry.local_path)
                if not os.path.isfile(file_path):
                    raise Exception('%s is not a valid file' % file_path)
                params_by_file_path[file_path] = name
                workspace_file_list.append(entry)

        data_file_store = DATA_FILE_STORE['DATA_FILE_STORE']
        if not data_file_store:
            raise Exception('No data file store found')
        stored_files = data_file_store.store_files(workspace_files, job_data.get_input_file_ids(), job_exe)

        # Organize results
        param_file_ids = {}  # Output parameter name -> file ID or [file IDs]
        for file_path in stored_files:
            file_id = stored_files[file_path]
            name = params_by_file_path[file_path]
            if name in param_file_ids:
                file_id_list = param_file_ids[name]
            else:
                file_id_list = []
                param_file_ids[name] = file_id_list
            file_id_list.append(file_id)

        # Create job results
        for name in param_file_ids:
            param_entry = param_file_ids[name]
            self.add_file_list_parameter(name, param_entry)
