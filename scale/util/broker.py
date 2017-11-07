from __future__ import unicode_literals

import re

from .exceptions import InvalidBrokerUrl

# Accepts broker URLs of decreasing specificity, as follows:
# transport://user:pass@host:port/vhost
# transport://host:port/vhost
# transport://host:port
# transport://host

REGEX_PATTERN = r'^(?P<type>[a-zA-Z]+):\/\/((?P<user_name>[^@:]+):(?P<password>[^@:]+)@)?(?P<address>[^@\/]+(:[0-9]+)?)\/?(?P<vhost>.+)?$'


class BrokerDetails(object):
    def __init__(self):
        self.user_name = None
        self.password = None
        self.address = None
        self.type = None
        self.vhost = None

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
            this.address = groups['address']

            if 'user_name' in groups and 'password' in groups:
                this.user_name = groups['user_name']
                this.password = groups['password']

            if 'vhost' in groups:
                this.vhost = groups['vhost']

            return this

        raise InvalidBrokerUrl

    def get_address(self):
        """Get extracted broker host and port or region depending on backend type
        
        :return: Broker host and port or region of backend
        :rtype: string
        """
        return self.address

    def get_password(self):
        """Get extracted password for broker authentication.
        
        May be None if credentials are not specified in broker URL.
        
        :return: Password for broker authentication
        :rtype: string or None
        """
        return self.password

    def get_type(self):
        """Get the transport broker type defined in URL

        :return: Transport type for broker connection
        :rtype: string
        """
        return self.type

    def get_user_name(self):
        """Get extracted user name for broker authentication.
        
        May be None if credentials are not specified in broker URL.
        
        :return: User name for broker authentication
        :rtype: string or None
        """
        return self.user_name

    def get_virtual_host(self):
        """Get extracted virtual host of broker backend

        May be None if virtual host is not specified in broker URL

        :return: Virtual host for broker connection
        :rtype: string or None
        """
        return self.vhost
