'''Defines the shared resources for a given job execution'''


JOB_ENVIRONMENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "version": {
            "description": "version of the job_interface schema",
            "type": "string"
        },
        "shared_resources": {
            "type": "array",
            "items": {"anyOf": [
                {"$ref": "#/definitions/shared_resource"},
                {"allOf": [
                    {"$ref": "#/definitions/shared_resource"},
                    {"$ref": "#/definitions/database"}
                ]}
            ]}
        },
    },
    "definitions": {
        "shared_resource": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "type": {"type": "string"}
            }
        },
        "database": {
            "type": "object",
            "properties": {
                "host": {"type": "string"},
                "user": {"type": "string"},
                "password": {"type": "string"}
            }
        }
    }
}


class JobEnvironment(object):
    '''Represents the shared resources available for a given job execution.  If the environment is invalid, a
    :class:`job.configuration.environment.exceptions.InvalidJobEnvirnoment` exception will be thrown.'''

    def __init__(self, json_env):
        '''Creates a JobEnvironment from the given dictionary.  The format is checked for correctness'''
        self.environment = json_env
        self.shared_resources_by_name = {}

    def get_dict(self):
        '''Returns the internal dictionary that represents this job environment

        :returns: The dictionary representing the environment
        :rtype: dict
        '''

        return self.environment
