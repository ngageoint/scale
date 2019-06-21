"""Defines a command message that creates job models"""
from __future__ import unicode_literals

import logging
from django.db import transaction
from django.utils.timezone import now

from data.data.data import Data
from data.data.value import JsonValue
from data.data.json.data_v6 import convert_data_to_v6_json, DataV6
from messaging.messages.message import CommandMessage
from queue.models import Queue
from trigger.models import TriggerEvent

logger = logging.getLogger(__name__)

STRIKE_JOB_TYPE = 'strike_job' # Message type for creating strike jobs
SCAN_JOB_TYPE = 'scan_job' # Message type for creating scan jobs

# This is the maximum number of jobs models that can fit in one message. This maximum ensures that every message of this
# type is less than 25 KiB long and that each message can be processed quickly.
MAX_NUM = 100

def create_scan_ingest_job_message(ingest_id, workspace_name, new_workspace_name, scan_id, file_name):
    """Creates a message to create the ingest job for a scan
    
    :param ingest_id: ID of the ingest
    :type ingest_id: int
    :param scan_id: The ID of the scan
    :type scan_id: int
    :param file_name: The name of the input file
    :type file_name: string
    """
    message = CreateIngest()
    message.create_ingest_type = SCAN_JOB_TYPE
    message.ingest_id = ingest_id
    message.workspace = workspace_name
    message.new_workspace = new_workspace_name
    message.scan_id = scan_id
    message.ingest_file_name = file_name
    
    return message
    
def create_strike_ingest_job_message(ingest_id, workspace_name, new_workspace_name, strike_id):
    """Creates a message to create the ingest job for a strike
    
    :param ingest_id: ID of the ingest
    :type ingest_id: int
    :param strike_id: The ID of the strike
    :type strike_id: int
    """
    message = CreateIngest()
    message.create_ingest_type = STRIKE_JOB_TYPE
    message.ingest_id = ingest_id
    message.workspace = workspace_name
    message.new_workspace = new_workspace_name
    message.strike_id = strike_id
    
    return message
    
class CreateIngest(CommandMessage):
    """Command message that creates the ingest job
    """
    
    def __init__(self):
        """Constructor
        """
        
        super(CreateIngest, self).__init__('create_ingest_jobs')
        
        # Fields applicable to all message types
        self.create_ingest_type = None
        self.ingest_id = None
        self.workspace = None
        self.new_workspace = None
        
        # Fields applicable to scan message types
        self.scan_id = None
        self.ingest_file_name = None
        
        # Fields applicable to strike message types
        self.strike_id = None
        
    def can_fit_more(self):
        """Indicates whether more jobs can fit in this message

        :return: True if more jobs can fit, False otherwise
        :rtype: bool
        """
        return True
        
    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """
        json_dict = {
            'create_ingest_type': self.create_ingest_type, 
            'ingest_id': self.ingest_id,
            'workspace': self.workspace
        }
        
        if self.new_workspace:
            json_dict['new_workspace'] = self.new_workspace
        
        if self.create_ingest_type == STRIKE_JOB_TYPE:
            json_dict['strike_id'] = self.strike_id
        elif self.create_ingest_type == SCAN_JOB_TYPE:
            json_dict['scan_id'] = self.scan_id
            json_dict['ingest_file_name'] = self.ingest_file_name
        
        return json_dict    
        
    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """
        
        message = CreateIngest()
        message.ingest_id = json_dict['ingest_id']
        message.create_ingest_type = json_dict['create_ingest_type']
        message.workspace = json_dict['workspace']
        
        if 'new_workspace' in json_dict:
            message.new_workspace = json_dict['new_workspace']
        if message.create_ingest_type == STRIKE_JOB_TYPE:
            message.strike_id = json_dict['strike_id']
        elif message.create_ingest_type == SCAN_JOB_TYPE:
            message.scan_id = json_dict['scan_id']
            message.ingest_file_name = json_dict['ingest_file_name']
        
        return message
        
    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """
        from ingest.models import Ingest
        ingest_job_type = Ingest.objects.get_ingest_job_type()
        
        # Grab the ingest object
        ingest = Ingest.objects.get(pk=self.ingest_id)
        
        when = ingest.transfer_ended if ingest.transfer_ended else now()
        desc = {'file_name': ingest.file_name}
        
        with transaction.atomic():
            # Create the appropriate triggerevent
            event = None
            if self.create_ingest_type == STRIKE_JOB_TYPE:
                ingest_id = ingest.id
                desc['strike_id'] = self.strike_id
                event =  TriggerEvent.objects.create_trigger_event('STRIKE_TRANSFER', None, desc, when)
            elif self.create_ingest_type == SCAN_JOB_TYPE:
                ingest_id = Ingest.objects.get(scan_id=self.scan_id, file_name=self.ingest_file_name).id
                event = TriggerEvent.objects.create_trigger_event('SCAN_TRANSFER', None, desc, when)
            
        data = Data()
        data.add_value(JsonValue('ingest_id', ingest_id))
        data.add_value(JsonValue('workspace', self.workspace))
        if self.new_workspace:
            data.add_value(JsonValue('new_workspace', self.new_workspace))
            
        ingest_job = Queue.objects.queue_new_job_v6(ingest_job_type, data, event)
        ingest.job = ingest_job
        ingest.status = 'QUEUED'
        ingest.save()
        
        from job.messages.process_job_input import create_process_job_input_messages
        from job.models import Job
        Queue.objects.queue_jobs([ingest_job])
        job = Job.objects.get_details(ingest_job.id)
        self.new_messages.extend(create_process_job_input_messages([job.pk]))
        
        return True
 
        