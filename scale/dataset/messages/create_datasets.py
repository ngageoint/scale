"""Defines a command message that creates dataset models"""
from __future__ import unicode_literals

import logging
from messaging.messages.message import CommandMessage

def create_dataset_message():
    """Creates a message to create a dataset of the given definition
    
    
    """
    
    
class CreateDatasets(CommandMessage):
    """Command message that creates dataset models
    
    Steps to complete:
    1. Perform locking in db transaction
    2. Look for existing datasets to see if message has already run
    3. Retrieve revision(s) for dataset to create
    4. Bulk create dataset
    5. DB transaction over, send message
    
    
    6. If dataset has data, and is trigger of job/recipe, and process_input true, send process_job_input
    """
    
    def __init__(self):
        """Constructor
        """
        
        super(CreateDatasets, self).__init__('create_datasets')
        
        # Fields applicable to all message types
        
        # applicable for dataset
        self.dataset_title = None
        self.dataset_name = None
        self.dataset_description = None
        self.dataset_id = None
        self.dataset_version = None
        
        
    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """
        
        json_dict = {}
        