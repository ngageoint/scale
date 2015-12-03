'''Defines functions for determining the media type of a file'''
import mimetypes


UNKNOWN_MEDIA_TYPE = u'application/octet-stream'
mimetypes.add_type(u'application/json', u'.json')
mimetypes.add_type(u'application/vnd.geo+json', u'.geojson')
mimetypes.add_type(u'image/x-hdf5-image', u'.h5')
mimetypes.add_type(u'image/x-nitf-image', u'.ntf')
mimetypes.add_type(u'application/xml', u'.xml')


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
