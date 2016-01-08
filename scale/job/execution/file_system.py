'''Defines methods for necessary file system interactions to perform job executions'''
from __future__ import unicode_literals

import logging
import os
import shutil

import job.settings as settings


logger = logging.getLogger(__name__)


def create_job_exe_dir(job_exe_id):
    '''Creates the top level directory for a job execution

    :param job_exe_id: The ID of the job execution
    :type job_exe_id: int
    '''

    job_exe_dir = get_job_exe_dir(job_exe_id)

    logger.info('Creating %s', job_exe_dir)
    os.makedirs(job_exe_dir, mode=0755)


def create_normal_job_exe_dir_tree(job_exe_id):
    '''Creates the directory tree structure for a non-system job execution (job with pre and post tasks). This method
    expects the top level job execution directory to have already been created.

    :param job_exe_id: The ID of the job execution
    :type job_exe_id: int
    '''

    job_exe_input_dir = get_job_exe_input_dir(job_exe_id)
    job_exe_input_data_dir = get_job_exe_input_data_dir(job_exe_id)
    job_exe_input_work_dir = get_job_exe_input_work_dir(job_exe_id)
    job_exe_output_dir = get_job_exe_output_dir(job_exe_id)
    job_exe_output_data_dir = get_job_exe_output_data_dir(job_exe_id)
    job_exe_output_work_dir = get_job_exe_output_work_dir(job_exe_id)

    logger.info('Creating %s', job_exe_input_dir)
    os.mkdir(job_exe_input_dir, 0755)
    logger.info('Creating %s', job_exe_input_data_dir)
    os.mkdir(job_exe_input_data_dir, 0755)
    logger.info('Creating %s', job_exe_input_work_dir)
    os.mkdir(job_exe_input_work_dir, 0755)

    logger.info('Creating %s', job_exe_output_dir)
    os.mkdir(job_exe_output_dir, 0755)
    logger.info('Creating %s', job_exe_output_data_dir)
    os.mkdir(job_exe_output_data_dir, 0755)
    logger.info('Creating %s', job_exe_output_work_dir)
    os.mkdir(job_exe_output_work_dir, 0755)


def delete_job_exe_dir(job_exe_id):
    '''Deletes the top level directory for a job execution

    :param job_exe_id: The ID of the job execution
    :type job_exe_id: int
    '''

    job_exe_dir = get_job_exe_dir(job_exe_id)

    if os.path.exists(job_exe_dir):
        logger.info('Deleting %s', job_exe_dir)
        os.rmdir(job_exe_dir)


def delete_normal_job_exe_dir_tree(job_exe_id):
    '''Deletes the directory tree structure for a non-system job execution (job with pre and post tasks)

    :param job_exe_id: The ID of the job execution
    :type job_exe_id: int
    '''

    job_exe_input_dir = get_job_exe_input_dir(job_exe_id)
    job_exe_input_data_dir = get_job_exe_input_data_dir(job_exe_id)
    job_exe_input_work_dir = get_job_exe_input_work_dir(job_exe_id)
    job_exe_output_dir = get_job_exe_output_dir(job_exe_id)
    job_exe_output_data_dir = get_job_exe_output_data_dir(job_exe_id)
    job_exe_output_work_dir = get_job_exe_output_work_dir(job_exe_id)

    if os.path.exists(job_exe_input_dir):
        if os.path.exists(job_exe_input_work_dir):
            logger.info('Deleting %s', job_exe_input_work_dir)
            os.rmdir(job_exe_input_work_dir)
        if os.path.exists(job_exe_input_data_dir):
            logger.info('Deleting %s', job_exe_input_data_dir)
            # Delete all input data
            shutil.rmtree(job_exe_input_data_dir)
        logger.info('Deleting %s', job_exe_input_dir)
        os.rmdir(job_exe_input_dir)

    if os.path.exists(job_exe_output_dir):
        if os.path.exists(job_exe_output_work_dir):
            logger.info('Deleting %s', job_exe_output_work_dir)
            os.rmdir(job_exe_output_work_dir)
        if os.path.exists(job_exe_output_data_dir):
            logger.info('Deleting %s', job_exe_output_data_dir)
            # Delete all output data
            shutil.rmtree(job_exe_output_data_dir)
        logger.info('Deleting %s', job_exe_output_dir)
        os.rmdir(job_exe_output_dir)


def get_job_exe_dir(job_exe_id):
    '''Returns the work directory for a job execution

    :param job_exe_id: The ID of the job execution
    :type job_exe_id: int
    :returns: The absolute path of the work directory
    :rtype: str
    '''

    node_work_dir = settings.NODE_WORK_DIR
    return os.path.join(node_work_dir, u'job_exe_%i' % job_exe_id)


def get_job_exe_input_dir(job_exe_id):
    '''Returns the input directory for a job execution

    :param job_exe_id: The ID of the job execution
    :type job_exe_id: int
    :returns: The absolute path of the input directory
    :rtype: str
    '''

    job_exe_dir = get_job_exe_dir(job_exe_id)
    return os.path.join(job_exe_dir, u'inputs')


def get_job_exe_input_data_dir(job_exe_id):
    '''Returns the directory for a job execution where input data should be written

    :param job_exe_id: The ID of the job execution
    :type job_exe_id: int
    :returns: The absolute path of the input data directory
    :rtype: str
    '''

    job_exe_input_dir = get_job_exe_input_dir(job_exe_id)
    return os.path.join(job_exe_input_dir, u'input_data')


def get_job_exe_input_work_dir(job_exe_id):
    '''Returns the directory for a job execution that the input workspaces can use as a work directory

    :param job_exe_id: The ID of the job execution
    :type job_exe_id: int
    :returns: The absolute path of the input work directory
    :rtype: str
    '''

    job_exe_input_dir = get_job_exe_input_dir(job_exe_id)
    return os.path.join(job_exe_input_dir, u'input_work')


def get_job_exe_output_dir(job_exe_id):
    '''Returns the output directory for a job execution

    :param job_exe_id: The ID of the job execution
    :type job_exe_id: int
    :returns: The absolute path of the output directory
    :rtype: str
    '''

    job_exe_dir = get_job_exe_dir(job_exe_id)
    return os.path.join(job_exe_dir, u'outputs')


def get_job_exe_output_data_dir(job_exe_id):
    '''Returns the directory for a job execution where output data should be written

    :param job_exe_id: The ID of the job execution
    :type job_exe_id: int
    :returns: The absolute path of the output data directory
    :rtype: str
    '''

    job_exe_output_dir = get_job_exe_output_dir(job_exe_id)
    return os.path.join(job_exe_output_dir, u'output_data')


def get_job_exe_output_work_dir(job_exe_id):
    '''Returns the directory for a job execution that the output workspace can use as a work directory

    :param job_exe_id: The ID of the job execution
    :type job_exe_id: int
    :returns: The absolute path of the output work directory
    :rtype: str
    '''

    job_exe_output_dir = get_job_exe_output_dir(job_exe_id)
    return os.path.join(job_exe_output_dir, u'output_work')
