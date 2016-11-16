"""Defines the class that manages the syncing of the scheduler with the job type models"""
from __future__ import unicode_literals

import threading

from job.models import JobType


class JobTypeManager(object):
    """This class manages the syncing of the scheduler with the job type models. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._job_types = {}  # {Job Type ID: Job Type}
        self._lock = threading.Lock()

    def get_job_type(self, job_type_id):
        """Returns the job type with the given ID, possibly None

        :param job_type_id: The ID of the job type
        :type job_type_id: str
        :returns: The job type for the given ID
        :rtype: :class:`job.models.JobType`
        """

        with self._lock:
            if job_type_id in self._job_types:
                return self._job_types[job_type_id]
            return None

    def get_job_types(self):
        """Returns a dict of all job types, stored by ID

        :returns: The dict of all job types
        :rtype: {int: :class:`job.models.JobType`}
        """

        with self._lock:
            return dict(self._job_types)

    def sync_with_database(self):
        """Syncs with the database to retrieve updated job type models
        """

        updated_job_types = {}
        for job_type in JobType.objects.all().iterator():
            updated_job_types[job_type.id] = job_type

        with self._lock:
            self._job_types = updated_job_types
