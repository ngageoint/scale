"""Defines the class that manages the syncing of the scheduler with the job type models"""
from __future__ import unicode_literals

import threading

from job.models import JobType
from node.resources.node_resources import NodeResources
from node.resources.resource import Cpus, Disk, Mem


# TODO: when we calculate duration averages for job types, create a new job type class that contains model, resources,
# stats, etc
class JobTypeManager(object):
    """This class manages the syncing of the scheduler with the job type models. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._job_type_resources = []
        self._job_types = {}  # {Job Type ID: Job Type}
        self._lock = threading.Lock()

    def generate_status_json(self, status_dict):
        """Generates the portion of the status JSON that describes the job types

        :param status_dict: The status JSON dict
        :type status_dict: dict
        """

        job_types_list = []
        status_dict['job_types'] = job_types_list
        with self._lock:
            for job_type in self._job_types.values():
                job_type_dict = {'id': job_type.id, 'name': job_type.name, 'version': job_type.version,
                                 'title': job_type.title, 'description': job_type.description,
                                 'is_system': job_type.is_system, 'icon_code': job_type.icon_code}
                job_types_list.append(job_type_dict)

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

    def get_job_type_resources(self):
        """Returns a list of all of the job type resource requirements

        :returns: The list of all of the job type resource requirements
        :rtype: list
        """

        with self._lock:
            return list(self._job_type_resources)

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

        update_job_type_resources = []
        updated_job_types = {}
        for job_type in JobType.objects.all().iterator():
            updated_job_types[job_type.id] = job_type
            resources = NodeResources([Cpus(job_type.cpus_required), Mem(job_type.mem_required),
                                       Disk(job_type.disk_out_const_required)])
            update_job_type_resources.append(resources)

        with self._lock:
            self._job_type_resources = update_job_type_resources
            self._job_types = updated_job_types


job_type_mgr = JobTypeManager()
