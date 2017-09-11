"""Defines the messaging service that handles the backend messaging"""
from __future__ import unicode_literals

import logging

from scheduler.manager import scheduler_mgr
from scheduler.tasks.services.messaging.message_handler_task import MessageHandlerTask
from scheduler.tasks.services.service import Service


logger = logging.getLogger(__name__)


class MessagingService(Service):
    """Service that handles the backend messaging"""

    def __init__(self):
        """Constructor"""

        super(MessagingService, self).__init__()

        self._name = 'Messaging'

    def get_desired_task_count(self):
        """See :meth:`scheduler.tasks.services.service.Service.get_desired_task_count`"""

        return scheduler_mgr.config.num_message_handlers

    def _create_service_task(self):
        """See :meth:`scheduler.tasks.services.service.Service._create_service_task`"""

        return MessageHandlerTask(scheduler_mgr.framework_id)
