#!/usr/bin/env python

import os
import sys
from urlparse import urlparse


uri = os.environ['ELASTICSEARCH_URL']
result = urlparse(uri)
infile = sys.argv[1]
outfile = sys.argv[2]

with open(infile) as file_handle:
    template = file_handle.read()


if result.username:
    template = template.replace('_ES_USERNAME_', 'user "{}"'.format(result.username))
else:
    template = template.replace('_ES_USERNAME_', '')
if result.password:
    template = template.replace('_ES_PASSWORD_', 'password "{}"'.format(result.password))
else:
    template = template.replace('_ES_PASSWORD_', '')
if result.port:
    template = template.replace('_ES_PORT_', 'port "{}"'.format(result.port))
else:
    template = template.replace('_ES_PORT_', '')
    
template = template.replace('_ES_HOST_', 'host "{}"'.format(result.hostname))

template = template.replace('_ES_SCHEME_', 'scheme "{}"'.format(result.scheme))


with open(outfile, 'w') as file_handle:
    file_handle.write(template)
    