class InvalidCommandMessage(Exception):
    """Exception indicating an invalid message identified during message processing"""

    pass


class CommandMessageExecuteFailure(Exception):
    """Exception indicating a failure signaled by execute function of CommandMessage"""

    pass
