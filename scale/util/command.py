"""Defines utility functions for executing commands on the command line."""
import logging
import subprocess
import re
from util.exceptions import UnbalancedBrackets

logger = logging.getLogger(__name__)


class CommandError(Exception):
    def __init__(self, msg, returncode=None):
        super(CommandError, self).__init__(msg)
        self.returncode = returncode


def execute_command_line(cmd_list):
    """Executes the given command list on the command line

    :param cmd_list: The list of commands
    :type cmd_list: []
    """

    logger.debug('Executing: %s', ' '.join(cmd_list))
    try:
        subprocess.check_output(cmd_list, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
        raise CommandError('Exit code %i: %s' % (ex.returncode, ex.output), ex.returncode)

def environment_expansion(env_map, cmd_string):
    """Performs environment variable expansion into command string

    The original preference was to use bash directly, eliminating the need for us to maintain
    regular expressions to mimic bash expansion logic. Unfortunately, the overhead of instantiating
    a sub-shell was prohibitively high on a large scale.

    We are instead handling merely a subset of expansion options:
    $VAR
    ${VAR}
    ${VAR/#/PREFIX}

    NOTE: All variables not matched remain unchanged

    WARNING: Resulting string should be treated as sensitive, due to the possibility
    of secrets being injected.

    :param env_map: map of environment variables to their values
    :type env_map: dict
    :param cmd_string: string to inject environment variables into
    :type cmd_string: str
    :return: string with parameters expanded
    :rtype: str
    :raises :class:`util.exceptions.UnbalancedBrackets`: if brackets are not balanced in cmd_string
    """

    # inline function to capture
    def dict_lookup(match):
        prefix = None

        value = match.group(0)
        key = match.group(1)
        key = key.lstrip('{').rstrip('}')

        # Handle special case for prefixed expansion
        if '/#/' in key:
            key, sep, prefix = key.split('/')
        if key in env_map:
            value = env_map[key]
            # If a prefix was found, insert at beginning of returned value
            if prefix:
                value = prefix + value

        return value

    if cmd_string.count('{') != cmd_string.count('}'):
        raise UnbalancedBrackets


    return re.sub(r'\$(\w+|\{[^}]*\})', dict_lookup, cmd_string)

