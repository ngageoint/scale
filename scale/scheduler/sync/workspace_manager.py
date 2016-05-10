"""Defines the class that manages the syncing of the scheduler with the workspace models"""
from __future__ import unicode_literals

import threading

from storage.models import Workspace


class WorkspaceManager(object):
    """This class manages the syncing of the scheduler with the workspace models. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._workspaces = {}  # {Workspace Name: Workspace}
        self._lock = threading.Lock()

    def get_workspaces(self):
        """Returns a dict of all workspaces, stored by name

        :returns: The dict of all workspaces
        :rtype: {string: :class:`storage.models.Workspace`}
        """

        with self._lock:
            return dict(self._workspaces)

    def sync_with_database(self):
        """Syncs with the database to retrieve updated workspace models
        """

        updated_workspaces = {}
        for workspace in Workspace.objects.all().iterator():
            updated_workspaces[workspace.name] = workspace

        with self._lock:
            self._workspaces = updated_workspaces
