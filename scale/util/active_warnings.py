class ActiveError(object):
    """This class represents an active error."""

    def __init__(self, error):
        """Constructor

        :param error: The error
        :type error: namedtuple
        """

        self.error = error
        self.started = None
        self.last_updated = None


class ActiveWarning(object):
    """This class represents an active warning."""

    def __init__(self, warning, description=None):
        """Constructor

        :param warning: The warning
        :type warning: namedtuple
        :param description: A specific description that overrides the general description
        :type description: string
        """

        self.warning = warning
        self.description = description
        self.started = None
        self.last_updated = None