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

        choice = random.choice(["string", "integer", "boolean", "object"])
        outputs = {}
        if choice == "string":
            next_choice = random.choice(["scale", "string", "elacs", "gnirts"])
            outputs['SCALE_STRING'] = next_choice
            print('The output is SCALE_STRING=%s' % next_choice, file=sys.stdout)
        elif choice == "integer":
            next_choice = random.choice([-1, 0, 1])
            outputs['SCALE_INTEGER'] = next_choice
            print('The output is SCALE_INTEGER=%d' % next_choice, file=sys.stdout)
        elif choice == "boolean":
            next_choice = random.choice([True, False])
            outputs['SCALE_BOOLEAN'] = next_choice
            print('The output is SCALE_BOOLEAN=%s' % next_choice, file=sys.stdout)
        elif choice == "object":
            next_choice = random.choice([{'next': 'then'}, {'next': 'else'}])
            outputs['SCALE_OBJECT'] = next_choice
            print('The output is SCALE_OBJECT=%s' % json.dumps(next_choice), file=sys.stdout)
        else:
            print('Not a valid choice! (stderr)', file=sys.stderr)

        with open(os.path.join(os.environ.get('OUTPUT_DIR', './'), 'seed.outputs.json'), 'w') as fout:
            json.dump(outputs, fout)

        # How does scale pick up on JSON output??
