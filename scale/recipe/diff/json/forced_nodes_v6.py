"""Manages the v6 forced nodes schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from recipe.diff.exceptions import InvalidDiff
from recipe.diff.forced_nodes import ForcedNodes


SCHEMA_VERSION = '6'


FORCED_NODES_SCHEMA = {
    'type': 'object',
    '$ref': '#/definitions/forced_nodes',
    'definitions': {
        'forced_nodes': {
            'description': 'Describes which nodes in this recipe should be forced to be reprocessed',
            'type': 'object',
            'required': ['all'],
            'additionalProperties': False,
            'properties': {
                'all': {
                    'description': 'Whether all nodes should be forced to be reprocessed',
                    'type': 'boolean',
                },
                'nodes': {
                    'description': 'The node names that should be forced to be reprocessed',
                    'type': 'array',
                    'items': {
                        'type': 'string',
                    },
                },
                'sub_recipes': {
                    'description': 'The sub-recipes that should be forced to be reprocessed, with recursive description for the sub-recipe\'s nodes',
                    'type': 'object',
                    'additionalProperties': {
                        '$ref': '#/definitions/forced_nodes'
                    },
                },
            },
        },
    },
}


def convert_forced_nodes_to_v6(forced_nodes):
    """Returns the v6 forced nodes JSON for the given forced nodes object

    :param forced_nodes: The forced nodes
    :type forced_nodes: :class:`recipe.diff.forced_nodes.ForcedNodes`
    :returns: The v6 forced nodes JSON
    :rtype: :class:`recipe.diff.json.forced_nodes_v6.ForcedNodesV6`
    """

    json_dict = _convert_forced_nodes_to_dict(forced_nodes)
    return ForcedNodesV6(forced_nodes=json_dict, do_validate=False)


def _convert_forced_nodes_to_dict(forced_nodes):
    """Returns the v6 JSON dict for the given forced nodes object

    :param forced_nodes: The forced nodes
    :type forced_nodes: :class:`recipe.diff.forced_nodes.ForcedNodes`
    :returns: The v6 JSON dict
    :rtype: dict
    """

    nodes = []
    sub_recipes = {}
    json_dict = {'version': '6', 'all': forced_nodes.all_nodes}

    if not forced_nodes.all_nodes:
        for node_name in forced_nodes.get_forced_node_names():
            nodes.append(node_name)
            sub_forced_nodes = forced_nodes.get_forced_nodes_for_subrecipe(node_name)
            if sub_forced_nodes:
                sub_recipes[node_name] = _convert_forced_nodes_to_dict(sub_forced_nodes)

        if nodes:
            json_dict['nodes'] = nodes
        if sub_recipes:
            json_dict['sub_recipes'] = sub_recipes

    return json_dict


class ForcedNodesV6(object):
    """Represents a v6 forced nodes JSON for the describing which nodes in a recipe should be forced to be reprocessed
    """

    def __init__(self, forced_nodes=None, do_validate=False):
        """Creates a v6 forced nodes JSON object from the given dictionary

        :param forced_nodes: The forced nodes JSON dict
        :type forced_nodes: dict
        :param do_validate: Whether to perform validation on the JSON schema
        :type do_validate: bool

        :raises :class:`recipe.diff.exceptions.InvalidDiff`: If the given forced nodes is invalid
        """

        if not forced_nodes:
            forced_nodes = {'all': False}
        self._forced_nodes = forced_nodes

        if 'version' not in self._forced_nodes:
            self._forced_nodes['version'] = SCHEMA_VERSION

        if self._forced_nodes['version'] != SCHEMA_VERSION:
            raise InvalidDiff('%s is an unsupported version number' % self._forced_nodes['version'])

        try:
            if do_validate:
                validate(self._forced_nodes, FORCED_NODES_SCHEMA)
        except ValidationError as ex:
            raise InvalidDiff('Invalid forced nodes: %s' % unicode(ex))

    def get_dict(self):
        """Returns the internal dictionary

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._forced_nodes

    def get_forced_nodes(self):
        """Returns the forced nodes object

        :returns: The forced nodes
        :rtype: :class:`recipe.diff.forced_nodes.ForcedNodes`
        """

        return self._get_forced_nodes_private(self._forced_nodes)

    def _get_forced_nodes_private(self, forced_nodes_dict):
        """A private helper method to recursively return the forced nodes object from the JSON dict

        :param forced_nodes_dict: The forced nodes JSON dict
        :type forced_nodes_dict: dict
        :returns: The forced nodes
        :rtype: :class:`recipe.diff.forced_nodes.ForcedNodes`
        """

        forced_nodes = ForcedNodes()

        if forced_nodes_dict['all']:
            forced_nodes.set_all_nodes()
        else:
            if 'nodes' in forced_nodes_dict:
                for node_name in forced_nodes_dict['nodes']:
                    forced_nodes.add_node(node_name)
            if 'sub_recipes' in forced_nodes_dict:
                for node_name, sub_recipe_dict in forced_nodes_dict['sub_recipes'].items():
                    forced_nodes.add_subrecipe(node_name, self._get_forced_nodes_private(sub_recipe_dict))

        return forced_nodes
