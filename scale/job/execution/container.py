"""Defines the methods for handling file systems in the job execution's local container volume"""
from __future__ import unicode_literals

import os

from storage.container import SCALE_ROOT_PATH


SCALE_JOB_EXE_INPUT_PATH = os.path.join(SCALE_ROOT_PATH, 'input_data')
SCALE_JOB_EXE_OUTPUT_PATH = os.path.join(SCALE_ROOT_PATH, 'input_data')
