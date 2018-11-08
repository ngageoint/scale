"""Defines methods that call the unversioned Mesos HTTP endpoints"""
from __future__ import unicode_literals

from node.resources.node_resources import NodeResources
from node.resources.resource import ScalarResource
from util.dcos import make_dcos_request


def get_agent_resources(master, agent_ids):
    """Returns the total resources for each of the given agents

    :param master: The address for the Mesos master
    :type master: `util.host.HostAddress`
    :param agent_ids: The set of agent IDs
    :type agent_ids: set
    :returns: The total resources for each agent stored by agent ID
    :rtype: dict
    """

    results = {}

    resp = make_dcos_request(master, '/slaves')

    for agent_dict in resp.json()['slaves']:
        agent_id = agent_dict['id']
        if agent_id in agent_ids:
            resource_list = []
            resource_dict = agent_dict['resources']
            for name in resource_dict:
                value = resource_dict[name]
                if isinstance(value, float):
                    resource_list.append(ScalarResource(name, value))
            resources = NodeResources(resource_list)
            results[agent_id] = resources

    return results
