'''Defines functions for determining the media type of a file'''
from __future__ import unicode_literals

import mimetypes


UNKNOWN_MEDIA_TYPE = 'application/octet-stream'
mimetypes.add_type('application/json', '.json')
mimetypes.add_type('application/vnd.geo+json', '.geojson')
mimetypes.add_type('image/x-hdf5-image', '.h5')
mimetypes.add_type('image/x-nitf-image', '.ntf')
mimetypes.add_type('application/xml', '.xml')


def get_media_type(file_name):
    '''Returns the media type of a file based upon the file's name

    :param file_name: The name of the file
    :type file_name: str
    :returns: The media type of the file
    :rtype: str
    '''

    media_type = mimetypes.guess_type(file_name, strict=False)[0]
    if not media_type:
        media_type = UNKNOWN_MEDIA_TYPE
    return media_type
