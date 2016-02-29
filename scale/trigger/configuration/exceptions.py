'''Defines exceptions that can occur when interacting with trigger rules'''


class InvalidTriggerRule(Exception):
    '''Exception indicating that the provided trigger rule configuration was invalid
    '''

    pass


class InvalidTriggerType(Exception):
    '''Exception indicating that the provided trigger rule type was invalid
    '''

    pass
