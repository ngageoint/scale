'''Defines utility methods for testing files and workspaces'''
import django.utils.timezone as timezone

from storage.models import ScaleFile, Workspace

WORKSPACE_NAME_COUNTER = 1
WORKSPACE_TITLE_COUNTER = 1


def create_file(file_name=u'my_test_file.txt', media_type=u'text/plain', file_size=100, file_path=None,
                            workspace=None):
    '''Creates a Scale file model for unit testing

    :returns: The file model
    :rtype: :class:`storage.models.ScaleFile`
    '''

    if not workspace:
        workspace = create_workspace()

    return ScaleFile.objects.create(file_name=file_name, media_type=media_type, file_size=file_size,
                                    file_path=file_path or u'file/path/' + file_name, workspace=workspace)


def create_workspace(name=None, title=None, base_url=None, is_active=True, archived=None):
    '''Creates a workspace model for unit testing

    :returns: The workspace model
    :rtype: :class:`storage.models.Workspace`
    '''

    if not name:
        global WORKSPACE_NAME_COUNTER
        name = u'test-workspace-%s' % str(WORKSPACE_NAME_COUNTER)
        WORKSPACE_NAME_COUNTER = WORKSPACE_NAME_COUNTER + 1
    if not title:
        global WORKSPACE_TITLE_COUNTER
        title = u'Test Workspace %s' % str(WORKSPACE_TITLE_COUNTER)
        WORKSPACE_TITLE_COUNTER = WORKSPACE_TITLE_COUNTER + 1
    if is_active is False and not archived:
        archived = timezone.now()

    return Workspace.objects.create(name=name, title=title, base_url=base_url, is_active=is_active, archived=archived)
