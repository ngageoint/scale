"""Defines methods that call the unversioned Mesos HTTP endpoints"""
from __future__ import unicode_literals

import json
import urllib2

from node.resources.node_resources import NodeResources
from node.resources.resource import ScalarResource


def get_agent_resources(hostname, port, agent_ids):
    """Returns the total resources for each of the given agents

    :param hostname: The hostname of the master
    :type hostname: str
    :param port: The port of the master
    :type port: int
    :param agent_ids: The set of agent IDs
    :type agent_ids: set
    :returns: The total resources for each agent stored by agent ID
    :rtype: dict
    """

    results = {}

    url = 'http://%s:%i/slaves' % (hostname, port)
    response = urllib2.urlopen(url)
    response_json = json.load(response)

    for agent_dict in response_json['slaves']:
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
