'''Error handlers for scale'''
from logging import Handler

import socket


class DatabaseLogHandler(Handler):
    '''This class inherits from the logging.Handler class to provide
       support for logging messages to a database table.
    '''

    # name of the model to log messages
    model = None

    def __init__(self, model=""):
        super(DatabaseLogHandler, self).__init__()
        self.model = model

    def emit(self, record):
        '''Saves the record object to a database using the Django model class

        :param record: Record object to save to the database
        :type record: LogRecord
        '''

        # get the model by name
        try:
            model = self.get_model(self.model)
        except:
            from error.models import LogEntry as model

        hostname = socket.getfqdn()
        levelname = record.levelname

        # Note if an exception occurred, the formatter will append it to
        # the message, so need to split the formatted string to get just
        # the message.
        formatted_message = self.format(record).split('\nTraceback')[0]
        log_entry = model(host=hostname, level=levelname,
                          message=formatted_message)

        # If there is exception information, add it to the 'LogEntry'
        if not record.exc_text is None:
            log_entry.stacktrace = record.exc_text

        # save log entry to database table
        log_entry.save()

    def handleError(self, record):
        '''Handles an exception that happened within the emit method

        :param record: Record object to save to the database
        :type record: LogRecord
        '''
        # silently ignore exceptions happening in emit method
        pass

    def get_model(self, model_name):
        '''Retrieves the given Django model given the name

        :param model_name: The name of the model to retrieve
        :type model_name: str
        '''
        names = model_name.split('.')
        python_module = __import__('.'.join(names[:-1]), fromlist=names[-1:])
        return getattr(python_module, names[-1])
