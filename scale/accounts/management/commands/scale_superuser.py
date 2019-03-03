"""Defines the command line method for running the Scale Hello job"""
from __future__ import unicode_literals
from __future__ import print_function

import os
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Command that initializes admin superuser in Scale
    """

    help = 'Set admin superuser password for Scale'

    def add_arguments(self, parser):
        parser.add_argument('-f', '--force', action='store_true',
                            help='Whether the superuser should be recreated.')
        parser.add_argument('-p', '--password', type=str, default=uuid.uuid4().hex,
                            help='Explicit password to apply.')

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.
        """

        new_password = options.get('password')

        try:
            user = User.objects.get(username='admin')
            if options.get('force'):
                user.first_name = 'Admin'
                user.last_name = 'User'
                user.set_password(new_password)
                user.save()
            else:
                user = None
                print('Existing admin user password left unchanged. Use --force flag to reset.')
        except User.DoesNotExist:
            user = User.objects.create_superuser(username='admin', first_name='Admin', last_name='User', email='',
                                                 password=new_password)

        if user:
            if settings.MESOS_SANDBOX:
                with open(os.path.join(settings.MESOS_SANDBOX, 'admin-pass.txt'), 'w') as pass_file:
                    pass_file.write(new_password)
            else:
                print('Superuser admin password set: %s' % (new_password,))


