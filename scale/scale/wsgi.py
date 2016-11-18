"""
WSGI config for scale project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scale.local_settings")

from django.core.wsgi import get_wsgi_application

_application = get_wsgi_application()

def application(environ, start_response):
    framework_name = os.environ.get('DCOS_PACKAGE_FRAMEWORK_NAME', 'scale')

    # If we are running behind Marathon LB we must set the HTTP_X_HAPROXY header to
    # configure the API to use the direct access context. Otherwise it assumes reverse proxy
    # behind DCOS Admin Router (Nginx)
    behind_haproxy = environ.get('HTTP_X_HAPROXY')
    if behind_haproxy:
        environ['SCRIPT_NAME'] = '/api'
    else:
        environ['SCRIPT_NAME'] = '/service/%s/api' % framework_name

    return _application(environ, start_response)
