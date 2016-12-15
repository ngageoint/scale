"""Defines a class for representing the meta-data description of a file or group of files in a job interface"""


class ScaleFileDescription(object):
    """Represents the meta-data description of a file or group of files in a job interface
    """

    def __init__(self):
        """Constructor
        """

        # NOTE: empty list means that all media types are accepted
        self.allowed_media_types = []

    def add_allowed_media_type(self, media_type):
        """Adds an allowed media type to the file description

        :param media_type: The allowed media type
        :type media_type: str
        """

        if media_type:
            self.allowed_media_types.append(media_type)

    def is_media_type_allowed(self, media_type):
        """Indicates whether the given media type is allowed by this file description

        :param media_type: The media type
        :type media_type: str
        :returns: True if the media type is allowed, False otherwise
        :rtype: bool
        """

        return not self.allowed_media_types or media_type in self.allowed_media_types
