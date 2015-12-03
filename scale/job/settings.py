'''Defines settings for running jobs on nodes'''
import os

from django.conf import settings

NODE_WORK_DIR = getattr(settings, u'NODE_WORK_DIR', os.path.join(os.sep, u'tmp', u'scale', u'work'))
