"""Defines a command message that creates job models"""
from __future__ import unicode_literals

import logging
from django.db import transaction
from django.utils.timezone import now

from data.data.data import Data
from data.data.value import JsonValue
from data.data.json.data_v6 import convert_data_to_v6_json, DataV6
from job.models import Job
from job.messages.process_job_input import create_process_job_input_messages
from messaging.messages.message import CommandMessage
from queue.models import Queue
from trigger.models import TriggerEvent

logger = logging.getLogger(__name__)

STRIKE_JOB_TYPE = 'strike_job' # Message type for creating strike jobs
SCAN_JOB_TYPE = 'scan_job' # Message type for creating scan jobs

def create_scan_ingest_job_message(ingest_id, scan_id):
    """Creates a message to create the ingest job for a scan
    
    :param ingest_id: ID of the ingest
    :type ingest_id: int
    :param scan_id: The ID of the scan
    :type scan_id: int
    """
    message = CreateIngest()
    message.create_ingest_type = SCAN_JOB_TYPE
    message.ingest_id = ingest_id
    message.scan_id = scan_id
    
    return message
    
def create_strike_ingest_job_message(ingest_id, strike_id):
    """Creates a message to create the ingest job for a strike
    
    :param ingest_id: ID of the ingest
    :type ingest_id: int
    :param strike_id: The ID of the strike
    :type strike_id: int
    """
    message = CreateIngest()
    message.create_ingest_type = STRIKE_JOB_TYPE
    message.ingest_id = ingest_id
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
        
        # Fields applicable to scan message types
        self.scan_id = None
        
        # Fields applicable to strike message types
        self.strike_id = None
        
    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """
        json_dict = {
            'create_ingest_type': self.create_ingest_type, 
            'ingest_id': self.ingest_id
        }
        
        if self.create_ingest_type == STRIKE_JOB_TYPE:
            json_dict['strike_id'] = self.strike_id
        elif self.create_ingest_type == SCAN_JOB_TYPE:
            json_dict['scan_id'] = self.scan_id
        
        return json_dict    
        
    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """
        
        message = CreateIngest()
        message.create_ingest_type = json_dict['create_ingest_type']
        message.ingest_id = json_dict['ingest_id']
        
        if message.create_ingest_type == STRIKE_JOB_TYPE:
            message.strike_id = json_dict['strike_id']
        elif message.create_ingest_type == SCAN_JOB_TYPE:
            message.scan_id = json_dict['scan_id']
        
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

        event = None
        ingest_id = ingest.id
        with transaction.atomic():
            # Create the appropriate triggerevent
            if self.create_ingest_type == STRIKE_JOB_TYPE:
                desc['strike_id'] = self.strike_id
                event =  TriggerEvent.objects.create_trigger_event('STRIKE_TRANSFER', None, desc, when)
            elif self.create_ingest_type == SCAN_JOB_TYPE:
                ingest_id = Ingest.objects.get(scan_id=self.scan_id, file_name=ingest.file_name).id
                desc['scan_id'] = self.scan_id
                event = TriggerEvent.objects.create_trigger_event('SCAN_TRANSFER', None, desc, when)
            
        data = Data()
        data.add_value(JsonValue('ingest_id', ingest_id))
        data.add_value(JsonValue('workspace', ingest.workspace.name))
        if ingest.new_workspace:
            data.add_value(JsonValue('new_workspace', ingest.new_workspace.name))

        ingest_job = None
        with transaction.atomic():
            ingest_job = Queue.objects.queue_new_job_v6(ingest_job_type, data, event)
            ingest.job = ingest_job
            ingest.status = 'QUEUED'
            ingest.save()
            
        # Send message to start processing job input (done outside the transaction to hope the job exists)
        # This can cause a race condition with a slow DB.
        job = Job.objects.get_details(ingest_job.id)

        return True
