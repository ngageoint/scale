"""Defines the fields for handling file systems in the local container volumes for ingest and Strike jobs"""
from __future__ import unicode_literals

import os

from storage.container import SCALE_ROOT_PATH


SCALE_INGEST_MOUNT_PATH = os.path.join(SCALE_ROOT_PATH, 'ingest_mount')
