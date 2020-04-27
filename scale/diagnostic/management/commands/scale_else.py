"""Defines the command line method for running the Scale Else job"""
from __future__ import unicode_literals
from __future__ import print_function

import sys

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Command that executes the Scale Else job
    """

    help = 'Prints out "Scale Else!"'

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.
        """

        print('Scale Else! (stderr)', file=sys.stderr)
        print('Scale Else! (stdout)', file=sys.stdout)