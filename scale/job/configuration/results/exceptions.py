'''Defines exceptions that can occur when interacting with a job results'''


class InvalidResultsManifest(Exception):
    '''Exception indicating that the provided definition of a results_manifest
    '''
    pass


class MissingRequiredOutput (Exception):
    '''The result manifests outputs do not match the required outputs or given inputs of the job
    '''

class MissingMultipleFileOutputParameter (Exception):
    '''The result manifests outputs do not match the required outputs or given inputs of the job
    '''

class MissingSingleFileOutputParameter (Exception):
    '''The result manifests output definition suggest that there should be multiple outputs, but only one was
    '''