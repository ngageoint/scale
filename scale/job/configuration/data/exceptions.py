'''Defines exceptions that can occur when interacting with job data'''


class InvalidConnection(Exception):
    '''Exception indicating that the provided job connection was invalid
    '''
    pass


class InvalidData(Exception):
    '''Exception indicating that the provided job data was invalid
    '''
    pass


class StatusError(Exception):
    '''Exception indicating that an operation cannot be completed due to the current job status.
    '''
    pass
