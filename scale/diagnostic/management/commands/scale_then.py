"""Defines the command line method for running the Scale Then job"""
from __future__ import unicode_literals
from __future__ import print_function

import sys

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Command that executes the Scale Then job
    """

    help = 'Prints out "Scale Then!"'

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.
        """

        print('Scale Then! (stderr)', file=sys.stderr)
        print('Scale Then! (stdout)', file=sys.stdout)