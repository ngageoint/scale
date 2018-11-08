"""Defines methods that call the unversioned Mesos HTTP endpoints"""
from __future__ import unicode_literals

import requests

from node.resources.node_resources import NodeResources
from node.resources.resource import ScalarResource


def get_agent_resources(master, auth, agent_ids):
    """Returns the total resources for each of the given agents

    :param master: The address for the Mesos master
    :type master: `util.host.HostAddress`
    :param auth: Authentication for traversing Strict boundary in DCOS EE
    :type auth: :class:`mesoshttp.acs.DCOSServiceAuth` or None
    :param agent_ids: The set of agent IDs
    :type agent_ids: set
    :returns: The total resources for each agent stored by agent ID
    :rtype: dict
    """

    results = {}

    resp = requests.get('%s://%s:%s/slaves' % (master.protocol, master.hostname, master.port),
                        auth=auth, verify=False)

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
