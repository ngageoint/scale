#@PydevCodeAnalysisIgnore
import django
 
from django.test import TestCase

from job.configuration.results.results_manifest.results_manifest import ResultsManifest
from job.configuration.results.exceptions import InvalidResultsManifest,\
    ResultsManifestAndInterfaceDontMatch
 
 
class TestResultsManifestConstructor(TestCase):
 
    def setUp(self):
        django.setup()
 
    def test_empty_results_manifest(self):
        json_manifest = {}
        #This should not throw an exception since it is valid
        ResultsManifest(json_manifest)
 
    def test_manifest_support_simple_file(self):
        json_manifest = {
            "version": "1.0",
            "files": [
                {"name":"foo", "path":"nfs:server//myfile.txt"}
            ]
        }
        try:
            #This should not throw an exception since it is valid
            ResultsManifest(json_manifest)
        except InvalidResultsManifest:
            self.fail(u'This simple json_manifest is valid')
 
    def test_manifest_supports_file_with_paths(self):
        json_manifest = {
            "version": "1.0",
            "files": [
                {"name":"foo", "paths":["nfs:server//myfile.txt"]}
            ]
        }
        try:
            #This should not throw an exception since it is valid
            ResultsManifest(json_manifest)
        except InvalidResultsManifest:
            self.fail(u'This simple json_manifest is valid')
 
    def test_invalid_results_manifest(self):
        json_manifest = {
            "version": "1.0",
            "files": [
                {"name":"foo", "path":"nfs:server//myfile.txt", "paths": ["nfs:server//why_do_i_have_path_and_paths"]}
            ]
        }
        try:
            ResultsManifest(json_manifest)
            self.fail(u'files in a results manifest should not have both path and paths')
        except InvalidResultsManifest:
            #This should throw an exception since it is invalid
            pass

    def test_manifest_version_1_1(self):
        json_manifest = {
            "version": "1.1",
            "output_data": [
                {
                    "name" : "output_file",
                    "file": {
                        "path" : "/tmp/job_exe_231/outputs/output.csv",
                        "geo_metadata": {
                            "data_started": "2015-05-15T10:34:12Z",
                            "data_ended" : "2015-05-15T10:36:12Z",
                            "geo_json": {
                                "type": "Polygon",
                                "coordinates": [ [ [ 1.0, 10.0 ], [ 2.0, 10.0 ], [ 2.0, 20.0 ],[ 1.0, 20.0 ], [ 1.0, 10.0 ] ] ]
                            }
                        }
                    }
                },
                {
                    "name" : "output_files",
                    "files": [
                        {
                            "path" : "/tmp/job_exe_231/outputs/output.csv",
                            "geo_metadata": {
                                "data_started": "2015-05-15T10:34:12Z",
                                "data_ended" : "2015-05-15T10:36:12Z",
                                "geo_json": {
                                    "type": "Polygon",
                                    "coordinates": [ [ [ 1.0, 10.0 ], [ 2.0, 10.0 ], [ 2.0, 20.0 ],[ 1.0, 20.0 ], [ 1.0, 10.0 ] ] ]
                                }
                            }
                        },
                        {
                            "path" : "/tmp/job_exe_231/outputs/output2.csv"
                        }
                    ]
                }
            ],
            "parse_results": [
                {
                    "filename" : "myfile.h5",
                    "data_started" : "2015-05-15T10:34:12Z",
                    "data_ended" : "2015-05-15T10:36:12Z",
                    "data_types" : ["H5", "VEG"]
                }
            ]
        }

        manifest = ResultsManifest(json_manifest)
 
 
class TestResultsManifestValidation(TestCase):
    def test_simple_validation(self):
        json_manifest = {
            "version": "1.0",
            "files": [
                {"name":"foo", "path":"nfs:server//myfile.txt"}
            ]
        }
        input_files = {
            "input_file": False
        }
        output_files = {
            "foo": (False, True)
        }
        manifest = ResultsManifest(json_manifest)
        manifest.validate(output_files)

    def test_simple_validation_1_1(self):
        json_manifest = {
            "version": "1.1",
            "output_data": [
                {
                    "name" : "output_file",
                    "file": {
                        "path" : "/tmp/job_exe_231/outputs/output.csv",
                        "geo_metadata": {
                            "data_started": "2015-05-15T10:34:12Z",
                            "data_ended" : "2015-05-15T10:36:12Z",
                            "geo_json": {
                                "type": "Polygon",
                                "coordinates": [ [ [ 1.0, 10.0 ], [ 2.0, 10.0 ], [ 2.0, 20.0 ],[ 1.0, 20.0 ], [ 1.0, 10.0 ] ] ]
                            }
                        }
                    }
                }
            ]
        }

        input_files = {
            "input_file": False
        }
        output_files = {
            "output_file": (False, True)
        }
        manifest = ResultsManifest(json_manifest)
        manifest.validate(output_files)
 
    def test_output_does_not_match(self):
        json_manifest = {
            "version": "1.0",
            "files": [
                {"name":"foo", "path":"nfs:server//myfile.txt"}
            ]
        }
        input_files = {
            "input_file": False
        }
        output_files = {
            "bar": (False, True)
        }
        manifest = ResultsManifest(json_manifest)
        try:
            manifest.validate(output_files)
            self.fail(u'The outputs do not match the manifest, there should be a failure')
        except ResultsManifestAndInterfaceDontMatch:
            pass
 
    def test_missing_optional_is_ok(self):
        json_manifest = {
            "version": "1.0",
            "files": [
                {"name":"foo", "path":"nfs:server//myfile.txt"}
            ]
        }
        input_files = {
            "input_file": False
        }
        output_files = {
            "foo": (False, True),
            "bar": (False, False)  #This is an optional file
        }
        manifest = ResultsManifest(json_manifest)
        try:
            manifest.validate(output_files)
        except ResultsManifestAndInterfaceDontMatch:
            self.fail(u'The missing an optional file')
 
    def test_missing_required_is_bad(self):
        json_manifest = {
            "version": "1.0",
            "files": [
                {"name":"foo", "path":"nfs:server//myfile.txt"}
            ]
        }
        input_files = {
            "input_file": False
        }
        output_files = {
            "foo": (False, True),
            "bar": (False, True)  #This is a missing required file
        }
        manifest = ResultsManifest(json_manifest)
        try:
            manifest.validate(output_files)
            self.fail(u'There is a missing required file.  Validation should have failed')
        except ResultsManifestAndInterfaceDontMatch:
            pass

class TestResultsManifestConversion(TestCase):

    def test_convert_1_0_to_1_1(self):
        json_manifest = {
            "version": "1.0",
            "files": [
                {"name" : "output_file", "path" : "/tmp/job_exe_231/outputs/output.csv"},
                {"name": "output_files", "paths": ["/tmp/job_exe_231/outputs/output.csv", "/tmp/job_exe_231/outputs/output2.csv"]}
            ],
            "parse_results": [
                {
                    "filename" : "myfile.h5",
                    "data_started" : "2015-05-15T10:34:12Z",
                    "data_ended" : "2015-05-15T10:36:12Z",
                    "data_types" : ["H5", "VEG"]
                }
            ],
            "errors": []
        }

        new_format = {
            "version": "1.1",
            "output_data": [
                {
                    "name" : "output_file",
                    "file": {
                        "path" : "/tmp/job_exe_231/outputs/output.csv"
                    }
                },
                {
                    "name" : "output_files",
                    "files": [
                        {
                            "path" : "/tmp/job_exe_231/outputs/output.csv"
                        },
                        {
                            "path" : "/tmp/job_exe_231/outputs/output2.csv"
                        }
                    ]
                }
            ],
            "parse_results": [
                {
                    "filename" : "myfile.h5",
                    "data_started" : "2015-05-15T10:34:12Z",
                    "data_ended" : "2015-05-15T10:36:12Z",
                    "data_types" : ["H5", "VEG"]
                }
            ],
            "errors": []
        }

        manifest = ResultsManifest(json_manifest)
        converted = manifest._convert_schema(json_manifest)
        self.assertEqual(converted, new_format)
