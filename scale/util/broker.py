from __future__ import unicode_literals

import re

from .exceptions import InvalidBrokerUrl

REGEX_PATTERN = r'^(?P<type>[a-zA-Z]+):\/\/((?P<user_name>[^@:]+):(?P<password>[^@:]+)@)?(?P<broker>[^@]+(:[0-9]+)?)\/\/$'


class BrokerDetails(object):
    def __init__(self):
        self.user_name = None
        self.password = None
        self.broker = None
        self.type = None

    @staticmethod
    def from_broker_url(broker_url):
        """Construct a BrokerDetails object from a broker URL
        
        :param broker_url: URL containing connection information to message broker
        :type broker_url: string
        :return: Instantiated object containing details within broker URL
        :rtype: 
        """

        match = re.match(REGEX_PATTERN, broker_url)
        if match:
            groups = match.groupdict()
            this = BrokerDetails()
            this.type = groups['type']
            this.broker = groups['broker']

            if 'user_name' in groups and 'password' in groups:
                this.user_name = groups['user_name']
                this.password = groups['password']

            return this
            
        raise InvalidBrokerUrl

    def get_broker(self):
        """Get extracted broker host and port or region depending on backend type
        
        :return: Broker host and port or region of backend
        :rtype: string
        """
        return self.broker
        
    def get_password(self):
        """Get extracted password for broker authentication.
        
        May be None if credentials are not specified in broker URL.
        
        :return: Password for broker authentication
        :rtype: string or None
        """
        return self.password
        
    def get_type(self):
        """
        """
        return self.type
        
    def get_user_name(self):
        """Get extracted user name for broker authentication.
        
        May be None if credentials are not specified in broker URL.
        
        :return: User name for broker authentication
        :rtype: string or None
        """
        return self.user_name