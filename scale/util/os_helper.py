"""Helper methods for os operations"""

import os, errno

def makedirs(path, mode=0755):
    try:
        os.makedirs(path, mode)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise