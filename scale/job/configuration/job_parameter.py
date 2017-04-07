
class DockerParam(object):
    """Represents a Docker parameter
    """

    def __init__(self, flag, value):
        """Creates a Docker parameter

        :param flag: The Docker flag of the parameter
        :type flag: string
        :param value: The value being passed to the Docker parameter
        :type value: string
        """

        self.flag = flag
        self.value = value


class TaskWorkspace(object):
    """Represents a workspace needed by a job task
    """

    def __init__(self, name, mode):
        """Creates a task workspace

        :param name: The name of the workspace
        :type name: string
        :param mode: The mode to use for the workspace, either 'ro' or 'rw'
        :type mode: string
        """

        self.name = name
        self.mode = mode


class TaskSetting(object):
    """Represents a setting needed by a job task
    """

    def __init__(self, name, value):
        """Creates a job task setting

        :param name: The name of the setting
        :type name: string
        :param value: The value to use for the setting
        :type value: string
        """

        self.name = name
        self.value = value
