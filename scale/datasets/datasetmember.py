SCHEMA_VERSION = '6'
DATASET_MEMBER_SCHEMA = {
    'type': 'object',
    'required': ['definition'],
    'additionalProperties': False,
    'properties': {
        'title': {
            'description': 'Title of the dataset',
            'type': 'string',
        },
        'description': {
            'description': 'Description of the dataset',
            'type': 'string'
        },
        'created_time': {
            
        }, 
        'definition': {
            'description': 'The data',
            'type': 'object',
        }
    }
}

class DataSetMemberDefinition(object):
    """
    Represents the definition of a DataSet object
    
    :keyword title: The title of this data set (optional)
    :type title: :class:`django.db.models.CharField`
    :keyword description: The description of the data set (optional)
    :type description: :class:`django.db.models.CharField`
    :keyword created_time:
    :type created_time: :class:`django.db.models.DateTimeField`
    """
    def __init__(self, definition=None, do_validate=True):
        """Constructor
        """
        title = None
        description = None
        created_time = None
        definition = {}