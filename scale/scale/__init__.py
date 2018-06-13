"""Django project root used for settings and deployment configuration."""

from __future__ import absolute_import
from collections import namedtuple

version_info_t = namedtuple(
    # major/minor/patch are semantic versions
    # qualifier is blank, rc1, etc. or " githash"
    'version_info_t', ('major', 'minor', 'patch', 'qualifier'),
)

VERSION = version_info_t(5, 5, 0, '-snapshot')

__version__ = '{0.major}.{0.minor}.{0.patch}{0.qualifier}'.format(VERSION)

# The Scale version is tagged on the Scale Docker image
# Docker tags cannot support + chars, so replace it with an underscore
__docker_version__ = __version__.replace('+', '_')

__author__ = 'NGA'
__contact__ = ''
__homepage__ = 'https://ngageoint.github.io/scale'
__docformat__ = 'restructuredtext'
