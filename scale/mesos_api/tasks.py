"""Defines the functions for generating Mesos tasks"""
from __future__ import unicode_literals

import logging
from mesos.interface import mesos_pb2
from django.conf import settings


logger = logging.getLogger(__name__)



def create_mesos_task(task):
    """Creates and returns a Mesos task from a Scale task

    :param task: The task
    :type task: :class:`job.execution.running.tasks.base_task.Task`
    :returns: The Mesos task
    :rtype: :class:`mesos_pb2.TaskInfo`
    """

    if task.uses_docker:
        return _create_docker_task(task)

    return _create_command_task(task)


def _create_base_task(task):
    """Creates and returns a base Mesos task from a Scale task

    :param task: The task
    :type task: :class:`job.execution.running.tasks.base_task.Task`
    :returns: The base Mesos task
    :rtype: :class:`mesos_pb2.TaskInfo`
    """

    mesos_task = mesos_pb2.TaskInfo()
    mesos_task.task_id.value = task.id
    mesos_task.slave_id.value = task.agent_id
    mesos_task.name = task.name
    resources = task.get_resources()

    if resources.cpus > 0:
        cpus = mesos_task.resources.add()
        cpus.name = 'cpus'
        cpus.type = mesos_pb2.Value.SCALAR
        cpus.scalar.value = resources.cpus

    if resources.mem > 0:
        mem = mesos_task.resources.add()
        mem.name = 'mem'
        mem.type = mesos_pb2.Value.SCALAR
        mem.scalar.value = resources.mem

    if resources.disk > 0:
        disk = mesos_task.resources.add()
        disk.name = 'disk'
        disk.type = mesos_pb2.Value.SCALAR
        disk.scalar.value = resources.disk

    return mesos_task


def _create_command_task(task):
    """Creates and returns a command-line Mesos task from a Scale task

    :param task: The task
    :type task: :class:`job.execution.running.tasks.base_task.Task`
    :returns: The command-line Mesos task
    :rtype: :class:`mesos_pb2.TaskInfo`
    """

    mesos_task = _create_base_task(task)
    mesos_task.command.value = task.command + ' ' + task.command_arguments

    return mesos_task


def _create_docker_task(task):
    """Creates and returns a Dockerized Mesos task from a Scale task

    :param task: The task
    :type task: :class:`job.execution.running.tasks.base_task.Task`
    returns: The Dockerized Mesos task
    rtype: :class:`mesos_pb2.TaskInfo`
    """

    mesos_task = _create_base_task(task)
    mesos_task.container.type = mesos_pb2.ContainerInfo.DOCKER
    mesos_task.container.docker.image = task.docker_image
    for param in task.docker_params:
        mesos_task.container.docker.parameters.add(key=param.flag, value=param.value)
    if task.is_docker_privileged:
        mesos_task.container.docker.privileged = True

    # TODO: Determine whether or not there is an entry point within
    # the docker image in order to pass in the docker container
    # command arguments correctly.
    # Right now we assume an entry point
    mesos_task.command.shell = False

    # parse through the docker arguments and add them
    # to the CommandInfo 'arguments' list
    arguments = task.command_arguments.split(" ")
    for argument in arguments:
        mesos_task.command.arguments.append(argument)
    mesos_task.command.arguments.append(settings.CONFIG_URI)

    mesos_task.container.docker.network = mesos_pb2.ContainerInfo.DockerInfo.Network.Value('BRIDGE')
    mesos_task.container.docker.force_pull_image = True

    return mesos_task
