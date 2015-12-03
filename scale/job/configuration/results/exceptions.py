'''Defines exceptions that can occur when interacting with a job results'''


class InvalidResultsManifest(Exception):
    '''Exception indicating that the provided definition of a results_manifest
    '''
    pass


class ResultsManifestAndInterfaceDontMatch(Exception):
    '''The result manifests outputs do not match the required outputs or given inputs of the job
    '''
