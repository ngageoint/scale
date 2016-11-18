"""Defines the methods for handling file systems in the job execution's local container volume"""
from __future__ import unicode_literals

import os

from storage.container import SCALE_ROOT_PATH


SCALE_JOB_EXE_INPUT_PATH = os.path.join(SCALE_ROOT_PATH, 'input_data')
SCALE_JOB_EXE_OUTPUT_PATH = os.path.join(SCALE_ROOT_PATH, 'output_data')


def get_job_exe_input_vol_name(job_exe):
    """Returns the container input volume name for the given job execution

    :param job_exe: The job execution model (must not be queued) with related job and job_type fields
    :type job_exe: :class:`job.models.JobExecution`
    :returns: The container input volume name
    :rtype: string

    :raises Exception: If the job execution is still queued
    """

    return '%s_input_data' % job_exe.get_cluster_id()


def get_job_exe_output_vol_name(job_exe):
    """Returns the container output volume name for the given job execution

    :param job_exe: The job execution model (must not be queued) with related job and job_type fields
    :type job_exe: :class:`job.models.JobExecution`
    :returns: The container output volume name
    :rtype: string

    :raises Exception: If the job execution is still queued
    """

    return '%s_output_data' % job_exe.get_cluster_id()


def get_workspace_volume_name(job_exe, workspace):
    """Returns the name of the workspace's container volume for the given job execution ID

    :param job_exe: The job execution model (must not be queued) with related job and job_type fields
    :type job_exe: :class:`job.models.JobExecution`
    :param workspace: The name of the workspace
    :type workspace: string
    :returns: The workspace's container volume name
    :rtype: string

    :raises Exception: If the job execution is still queued
    """

    return '%s_wksp_%s' % (job_exe.get_cluster_id(), workspace)
