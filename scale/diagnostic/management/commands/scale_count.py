"""Defines the command line method for running the Scale Count job"""
from __future__ import unicode_literals
from __future__ import print_function

import sys

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Command that executes the Scale Count job
    """

    help = 'Prints out number 0 through 99 for stdout, stderr and interleaved'

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.
        """

        for i in range(100):
            print(i, file=sys.stdout)

        for i in range(100):
            print(i, file=sys.stderr)

        for i in range(100):
            print(i, file=sys.stdout if i % 2 else sys.stderr)
