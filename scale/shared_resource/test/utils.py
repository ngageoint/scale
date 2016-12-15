"""Defines utility methods for testing nodes"""
import job.test.utils as job_test_utils
from shared_resource.models import SharedResource, SharedResourceRequirement

NAME_COUNTER = 1


def create_resource(name=None, limit=None, is_global=True):
    """Creates a shared resource model for unit testing

    :returns: The shared resource model
    :rtype: :class:`shared_resource.models.SharedResource`
    """

    if not name:
        global NAME_COUNTER
        name = u'resource-%i' % NAME_COUNTER
        NAME_COUNTER = NAME_COUNTER + 1

    return SharedResource.objects.create(name=name, limit=limit, is_global=is_global)


def create_requirement(job_type=None, shared_resource=None, usage=None):
    """Creates a shared resource requirement model for unit testing

    :returns: The shared resource requirement model
    :rtype: :class:`shared_resource.models.SharedResourceRequirement`
    """

    if not job_type:
        job_type = job_test_utils.create_job_type()
    if not shared_resource:
        shared_resource = create_resource()

    return SharedResourceRequirement.objects.create(job_type=job_type, shared_resource=shared_resource, usage=usage)
