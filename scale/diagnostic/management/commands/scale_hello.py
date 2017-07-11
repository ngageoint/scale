"""Defines the command line method for running the Scale Hello job"""
from __future__ import unicode_literals
from __future__ import print_function

import sys

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Command that executes the Scale Hello job
    """

    help = 'Prints out "Hello Scale!"'

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.
        """

        print('Hello Scale! (stderr)', file=sys.stderr)
        print('Hello Scale! (stdout)', file=sys.stdout)