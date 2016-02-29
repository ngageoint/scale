'''Defines utility functions for executing commands on the command line.'''
import logging
import subprocess


logger = logging.getLogger(__name__)


class CommandError(Exception):
    def __init__(self, msg, returncode=None):
        super(CommandError, self).__init__(msg)
        self.returncode = returncode


def execute_command_line(cmd_list):
    '''Executes the given command list on the command line

    :param cmd_list: The list of commands
    :type cmd_list: list
    '''

    logger.debug('Executing: %s', ' '.join(cmd_list))
    try:
        subprocess.check_output(cmd_list, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
        raise CommandError('Exit code %i: %s' % (ex.returncode, ex.output), ex.returncode)
