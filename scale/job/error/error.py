"""Defines the class for representing a job error"""
from __future__ import absolute_import
from __future__ import unicode_literals

import logging

from error.models import Error


logger = logging.getLogger(__name__)


class JobError(object):
    """Represents a job error that would appear in a job type's error mapping"""

    def __init__(self, job_type_name, name, title=None, description=None, category='ALGORITHM'):
        """Creates a job error

        :param job_type_name: The job type name
        :type job_type_name: string
        :param name: The error name
        :type name: string
        :param title: The error title
        :type title: string
        :param description: The error description
        :type description: string
        :param category: The error category
        :type category: string
        """

        self.job_type_name = job_type_name
        self.name = name
        self.title = title
        self.description = description
        self.category = category

    def create_model(self):
        """Creates an error model representing this job error

        :returns: The error model
        :rtype: :class:`error.models.Error`
        """

        error_model = Error()
        error_model.name = self.name
        error_model.job_type_name = self.job_type_name
        error_model.title = self.title
        error_model.description = self.description
        error_model.category = self.category
        
        return error_model
