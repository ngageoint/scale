'''Defines utility exceptions'''


class RollbackTransaction(Exception):
    '''Exception that can be thrown and swallowed to explicitly rollback a transaction
    '''

    pass
