'''Defines methods for necessary file system interactions to perform job executions'''
import os

import job.settings as settings


def get_job_exe_dir(job_exe_id, node_work_dir):
    '''Returns the work directory for a job execution

    :param job_exe_id: The ID of the job execution
    :type job_exe_id: int
    :param node_work_dir: The absolute path of the work directory for the node
    :type node_work_dir: str
    :returns: The absolute path of the work directory
    :rtype: str
    '''

    return os.path.join(node_work_dir, u'job_exe_%i' % job_exe_id)


def get_job_exe_input_dir(job_exe_id, node_work_dir):
    '''Returns the input directory for a job execution

    :param job_exe_id: The ID of the job execution
    :type job_exe_id: int
    :param node_work_dir: The absolute path of the work directory for the node
    :type node_work_dir: str
    :returns: The absolute path of the input directory
    :rtype: str
    '''

    job_exe_dir = get_job_exe_dir(job_exe_id, node_work_dir)
    return os.path.join(job_exe_dir, u'inputs')


def get_job_exe_input_data_dir(job_exe_id):
    '''Returns the directory for a job execution where input data should be written

    :param job_exe_id: The ID of the job execution
    :type job_exe_id: int
    :returns: The absolute path of the input data directory
    :rtype: str
    '''

    node_work_dir = settings.NODE_WORK_DIR
    job_exe_input_dir = get_job_exe_input_dir(job_exe_id, node_work_dir)
    return os.path.join(job_exe_input_dir, u'input_data')


def get_job_exe_input_work_dir(job_exe_id):
    '''Returns the directory for a job execution that the input workspaces can use as a work directory

    :param job_exe_id: The ID of the job execution
    :type job_exe_id: int
    :returns: The absolute path of the input work directory
    :rtype: str
    '''

    node_work_dir = settings.NODE_WORK_DIR
    job_exe_input_dir = get_job_exe_input_dir(job_exe_id, node_work_dir)
    return os.path.join(job_exe_input_dir, u'input_work')


def get_job_exe_output_dir(job_exe_id, node_work_dir):
    '''Returns the output directory for a job execution

    :param job_exe_id: The ID of the job execution
    :type job_exe_id: int
    :param node_work_dir: The absolute path of the work directory for the node
    :type node_work_dir: str
    :returns: The absolute path of the output directory
    :rtype: str
    '''

    job_exe_dir = get_job_exe_dir(job_exe_id, node_work_dir)
    return os.path.join(job_exe_dir, u'outputs')


def get_job_exe_output_data_dir(job_exe_id):
    '''Returns the directory for a job execution where output data should be written

    :param job_exe_id: The ID of the job execution
    :type job_exe_id: int
    :returns: The absolute path of the output data directory
    :rtype: str
    '''

    node_work_dir = settings.NODE_WORK_DIR
    job_exe_output_dir = get_job_exe_output_dir(job_exe_id, node_work_dir)
    return os.path.join(job_exe_output_dir, u'output_data')


def get_job_exe_output_work_dir(job_exe_id):
    '''Returns the directory for a job execution that the output workspace can use as a work directory

    :param job_exe_id: The ID of the job execution
    :type job_exe_id: int
    :returns: The absolute path of the output work directory
    :rtype: str
    '''

    node_work_dir = settings.NODE_WORK_DIR
    job_exe_output_dir = get_job_exe_output_dir(job_exe_id, node_work_dir)
    return os.path.join(job_exe_output_dir, u'output_work')
