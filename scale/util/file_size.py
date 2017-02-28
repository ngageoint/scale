"""Defines a utility method for displaying file sizes"""

SIZE_LABELS = ['bytes', 'KiB', 'MiB', 'GiB', 'TiB']
MAX_LABEL_INDEX = len(SIZE_LABELS) - 1


def file_size_to_string(file_size):
    """Returns the given file size as a human-readable string

    :param file_size: The file size
    :type file_size: long
    :returns: The human-readable string
    :rtype: string
    """

    label_index = 0
    factor = 1024.0
    while label_index < MAX_LABEL_INDEX and file_size > factor:
        file_size /= factor
        label_index += 1
    return '%.2f %s' % (file_size, SIZE_LABELS[label_index])
