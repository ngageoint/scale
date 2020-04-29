"""Defines the command line method for running the Scale If job"""
from __future__ import unicode_literals
from __future__ import print_function

import json
import os
import random
import sys

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Command that executes the Scale If job
    """

    help = 'Produces a JSON output"'

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.
        """

        outputs = {}

        choice = random.choice(["scale", "string", "elacs", "gnirts"])
        outputs['SCALE_STRING'] = choice
        print('The output is SCALE_STRING=%s' % choice, file=sys.stdout)
        choice = random.choice([-1, 0, 1])
        outputs['SCALE_INTEGER'] = choice
        print('The output is SCALE_INTEGER=%d' % choice, file=sys.stdout)
        choice = random.choice([True, False])
        outputs['SCALE_BOOLEAN'] = choice
        print('The output is SCALE_BOOLEAN=%s' % choice, file=sys.stdout)
        choice = random.choice([{'next': 'then'}, {'next': 'else'}])
        outputs['SCALE_OBJECT'] = choice
        print('The output is SCALE_OBJECT=%s' % json.dumps(choice), file=sys.stdout)

        with open(os.path.join(os.environ.get('OUTPUT_DIR', './'), 'seed.outputs.json'), 'w') as fout:
            json.dump(outputs, fout)

        # How does scale pick up on JSON output??
