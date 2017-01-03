"""Provides models and managers for for shared resources"""
from __future__ import unicode_literals

from django.db import models
from django.db.models import Q
from django.db.models.aggregates import Sum
import djorm_pgjson

from job.models import JobType
from job.models import JobExecution
from node.models import Node


class SharedResourceManager(models.Manager):
    """Provides additional methods for managing shared resources"""

    def get_resource_remaining(self, resource):
        """Gets the remaining amount of a resource by looking at running jobs
        :param resource: The resource that we are looking at to determine usage
        :type resource: :class:`resource.model.SharedResource`
        :returns: the amount of resources remaining
        :rtype: float
        """
        job_types_that_use_resource = JobType.objects.filter(sharedresourcerequirement__shared_resource=resource)
        running_jobs = JobExecution.objects.get_running_job_exes()
        jobs_using_resource = running_jobs.filter(job__job_type__in=job_types_that_use_resource)
        if not jobs_using_resource:
            return resource.limit

        job_usage_sum = Sum('job__job_type__sharedresourcerequirement__usage')
        resource_aggr = jobs_using_resource.aggregate(total_usage=job_usage_sum)
        return resource.limit - resource_aggr['total_usage']

    def runnable_job_types(self, node):
        """Finds the job types that are runnable on a node based on shared resources
        :param node: The node that is using the resources
        :type node: :class:`node.models.Node`
        :returns: A new queryset containing :class:`job.models.JobType` objects filtered by available resources
        :rtype: :class:`django.db.models.query.QuerySet`
        """
        # Find unavailable_resources by node access
        available_resources = SharedResource.objects.filter(Q(is_global=True) | Q(nodes__pk=node.pk))
        unavailable_resources = SharedResource.objects.exclude(id__in=available_resources)

        # filter job_types by unavailable resources
        unavailable_requirements = SharedResourceRequirement.objects.filter(shared_resource__in=unavailable_resources)
        available_job_types = JobType.objects.exclude(sharedresourcerequirement__in=unavailable_requirements)

        # Find resources requirements that are too high
        for resource in available_resources:
            if resource.limit is None:
                continue
            remaining = self.get_resource_remaining(resource)
            unavailable_requirements = SharedResourceRequirement.objects.filter(Q(shared_resource=resource) &
                                                                                Q(usage__gt=remaining))
            available_job_types = available_job_types.exclude(sharedresourcerequirement__in=unavailable_requirements)

        return available_job_types


class SharedResource(models.Model):
    """Represents a resource available to the system that multiple nodes may share
    if limit is populated it is the upper limit of available resources of this type
    examples may be: network usage, database access, and licenses
    keyword name: The unique name of the global resource
    keyword description: A description of the global resource
    """
    name = models.CharField(db_index=True, max_length=100, unique=True)
    title = models.CharField(blank=True, max_length=100, null=True)
    description = models.CharField(max_length=250, blank=True, null=True)
    limit = models.FloatField(null=True)
    json_config = djorm_pgjson.fields.JSONField(null=True)

    is_global = models.BooleanField(default=True)
    nodes = models.ManyToManyField(Node)

    objects = SharedResourceManager()

    class Meta(object):
        """meta information for the db"""
        db_table = 'shared_resource'


class SharedResourceRequirement(models.Model):
    """A requirement for a shared resource.  A job is an example of something that can have a global resource
    requirement.  The requirement may include a usage amount.  As an example you could require 1.3 Gbps from
    a shared network pipe.
    """
    shared_resource = models.ForeignKey(SharedResource)
    job_type = models.ForeignKey(JobType)
    usage = models.FloatField(null=True)
