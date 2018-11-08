from __future__ import absolute_import
from __future__ import unicode_literals

import json

import requests
from django.conf import settings

from mesoshttp.acs import DCOSServiceAuth

DCOS_AUTH = None
DCOS_VERIFY = True
if settings.SERVICE_SECRET:
    # We are in Enterprise mode and using service account
    DCOS_AUTH = DCOSServiceAuth((json.loads(settings.SERVICE_SECRET)))

    cert_file = 'dcos-ca.crt'
    response = requests.get('https://leader.mesos/ca/' + cert_file, verify=False)

    if response.status_code == 200:
        with open(cert_file, 'w') as cert:
            cert.write(response.text)
    DCOS_VERIFY = cert_file

def make_dcos_request(host_address, relative_url, params=None):
    """Makes a requests that is capable of traversing DCOS EE Strict boundary

    :param master: The address for the Mesos master
    :type master: `util.host.HostAddress`
    :param relative_url: URL path relative to the base address
    :type relative_url: basestring
    :param params: The query parameters for request
    :type params: dict
    :returns: The request response object
    :rtype: :class:`requests.Response`
    """

    return requests.get('%s://%s:%s%s' % (host_address.protocol,
                                          host_address.hostname,
                                          host_address.port,
                                          relative_url),
                        param=params,
                        auth=DCOS_AUTH,
                        verify=DCOS_VERIFY)