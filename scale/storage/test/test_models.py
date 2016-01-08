#@PydevCodeAnalysisIgnore
import os

import django
from django.test import TestCase
from django.utils.text import get_valid_filename
from django.utils.timezone import utc
from django.db import transaction
from mock import MagicMock, patch

import datetime
import django.contrib.gis.geos as geos
import storage.test.utils as storage_test_utils
from storage.exceptions import ArchivedWorkspace, DeletedFile, InvalidDataTypeTag
from storage.models import ScaleFile, CountryData


class TestScaleFileUpdateUUID(TestCase):

    def setUp(self):
        django.setup()

    def test_none(self):
        '''Tests calling update_uuid with no arguments.'''

        the_file = ScaleFile()
        self.assertRaises(ValueError, the_file.update_uuid)

    def test_one_string(self):
        '''Tests calling update_uuid with a single string.'''

        the_file = ScaleFile()
        the_file.update_uuid(u'test.txt')

        self.assertEqual(len(the_file.uuid), 32)
        self.assertEqual(the_file.uuid, u'dd18bf3a8e0a2a3e53e2661c7fb53534')

    def test_multi_strings(self):
        '''Tests calling update_uuid with multiple strings.'''

        the_file = ScaleFile()
        the_file.update_uuid(u'test.txt', u'test1', u'test2')

        self.assertEqual(len(the_file.uuid), 32)
        self.assertEqual(the_file.uuid, u'8ff66acfc019330bba973b408c63ad15')

    def test_objects(self):
        '''Tests calling update_uuid with multiple object types.'''

        the_file = ScaleFile()
        the_file.update_uuid(u'test.txt', 1, True, {u'key': u'value'})

        self.assertEqual(len(the_file.uuid), 32)
        self.assertEqual(the_file.uuid, u'ee6535359fbe02d50589a823951eb491')

    def test_partial(self):
        '''Tests calling update_uuid with some ignored None types.'''

        the_file1 = ScaleFile()
        the_file1.update_uuid(u'test.txt', u'test')

        the_file2 = ScaleFile()
        the_file2.update_uuid(u'test.txt', None, u'test', None)

        self.assertEqual(the_file1.uuid, the_file2.uuid)


class TestScaleFileAddDataTypeTag(TestCase):

    def setUp(self):
        django.setup()

    def test_valid(self):
        '''Tests calling add_data_type_tag() with valid tags'''

        the_file = ScaleFile()
        the_file.add_data_type_tag(u'Hello-1')
        the_file.add_data_type_tag(u'foo_BAR')
        tags = the_file.get_data_type_tags()

        correct_set = set()
        correct_set.add(u'Hello-1')
        correct_set.add(u'foo_BAR')

        self.assertSetEqual(tags, correct_set)

    def test_invalid(self):
        '''Tests calling add_data_type_tag() with invalid tags'''

        the_file = ScaleFile()

        self.assertRaises(InvalidDataTypeTag, the_file.add_data_type_tag, u'my.invalid.tag')
        self.assertRaises(InvalidDataTypeTag, the_file.add_data_type_tag, u'my\invalid\tag!')


class TestScaleFileGetDataTypeTags(TestCase):

    def setUp(self):
        django.setup()

    def test_tags(self):
        '''Tests calling get_data_type_tags() with tags'''

        the_file = ScaleFile(data_type=u'A,B,c')
        tags = the_file.get_data_type_tags()

        correct_set = set()
        correct_set.add(u'A')
        correct_set.add(u'B')
        correct_set.add(u'c')

        self.assertSetEqual(tags, correct_set)

    def test_no_tags(self):
        '''Tests calling get_data_type_tags() with no tags'''

        the_file = ScaleFile()
        tags = the_file.get_data_type_tags()

        self.assertSetEqual(tags, set())


class TestScaleFileManagerCleanupDownloadDir(TestCase):

    def setUp(self):
        django.setup()

    @patch('storage.models.Workspace.objects.all')
    @patch('storage.models.os.path.exists')
    @patch('storage.models.os.rmdir')
    def test_success(self, mock_rmdir, mock_exists, mock_workspaces):
        '''Tests calling ScaleFileManager.cleanup_download_dir() successfully'''

        download_dir = os.path.join('download', 'dir')
        work_dir = os.path.join('work', 'dir')

        workspace_1 = storage_test_utils.create_workspace()
        workspace_1.cleanup_download_dir = MagicMock()
        workspace_1_work_dir = ScaleFile.objects._get_workspace_work_dir(work_dir, workspace_1)

        workspace_2 = storage_test_utils.create_workspace()
        workspace_2.cleanup_download_dir = MagicMock()
        workspace_2_work_dir = ScaleFile.objects._get_workspace_work_dir(work_dir, workspace_2)

        def new_exists(path):
            return path == workspace_1_work_dir
        mock_exists.side_effect = new_exists

        def new_workspaces():
            return [workspace_1, workspace_2]
        mock_workspaces.side_effect = new_workspaces

        ScaleFile.objects.cleanup_download_dir(download_dir, work_dir)

        workspace_1.cleanup_download_dir.assert_called_once_with(download_dir, workspace_1_work_dir)
        mock_rmdir.assert_called_once_with(workspace_1_work_dir)
        # Workspace 2 should not be cleaned up because os.path.exists() returns false
        self.assertFalse(workspace_2.cleanup_download_dir.called)


class TestScaleFileManagerCleanupUploadDir(TestCase):

    def setUp(self):
        django.setup()

    @patch('storage.models.os.listdir')
    @patch('storage.models.os.path.exists')
    @patch('storage.models.os.rmdir')
    def test_success(self, mock_rmdir, mock_exists, mock_listdir):
        '''Tests calling ScaleFileManager.cleanup_upload_dir() successfully'''

        upload_dir = os.path.join('upload', 'dir')
        work_dir = os.path.join('work', 'dir')

        workspace_1 = storage_test_utils.create_workspace()
        workspace_1.cleanup_upload_dir = MagicMock()
        workspace_1_work_dir = ScaleFile.objects._get_workspace_work_dir(work_dir, workspace_1)

        def new_exists(path):
            return path == workspace_1_work_dir
        mock_exists.side_effect = new_exists

        def new_listdir(path):
            return []
        mock_listdir.side_effect = new_listdir

        ScaleFile.objects.cleanup_upload_dir(upload_dir, work_dir, workspace_1)

        workspace_1.cleanup_upload_dir.assert_called_once_with(upload_dir, workspace_1_work_dir)


class TestScaleFileManagerDownloadFiles(TestCase):

    def setUp(self):
        django.setup()

    @patch('storage.models.os.makedirs')
    def test_success(self, mock_makedirs):
        '''Tests calling ScaleFileManager.download_files() successfully'''

        download_dir = os.path.join('download', 'dir')
        work_dir = os.path.join('work', 'dir')

        workspace_1 = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(workspace=workspace_1)
        local_path_1 = u'my/local/path/file.txt'
        file_2 = storage_test_utils.create_file(workspace=workspace_1)
        local_path_2 = u'another/local/path/file.txt'
        file_3 = storage_test_utils.create_file(workspace=workspace_1)
        local_path_3 = u'another/local/path/file.json'
        workspace_1.setup_download_dir = MagicMock()
        workspace_1.download_files = MagicMock()
        workspace_1_work_dir = ScaleFile.objects._get_workspace_work_dir(work_dir, workspace_1)

        workspace_2 = storage_test_utils.create_workspace()
        file_4 = storage_test_utils.create_file(workspace=workspace_2)
        local_path_4 = u'my/local/path/4/file.txt'
        file_5 = storage_test_utils.create_file(workspace=workspace_2)
        local_path_5 = u'another/local/path/5/file.txt'
        workspace_2.setup_download_dir = MagicMock()
        workspace_2.download_files = MagicMock()
        workspace_2_work_dir = ScaleFile.objects._get_workspace_work_dir(work_dir, workspace_2)

        files = [(file_1, local_path_1), (file_2, local_path_2), (file_3, local_path_3), (file_4, local_path_4),
                 (file_5, local_path_5)]
        ScaleFile.objects.download_files(download_dir, work_dir, files)

        workspace_1.setup_download_dir.assert_called_once_with(download_dir, workspace_1_work_dir)
        workspace_1.download_files.assert_called_once_with(download_dir, workspace_1_work_dir,
                                                           [(file_1.file_path, local_path_1),
                                                            (file_2.file_path, local_path_2),
                                                            (file_3.file_path, local_path_3)])
        workspace_2.setup_download_dir.assert_called_once_with(download_dir, workspace_2_work_dir)
        workspace_2.download_files.assert_called_once_with(download_dir, workspace_2_work_dir,
                                                           [(file_4.file_path, local_path_4),
                                                            (file_5.file_path, local_path_5)])

    def test_inactive_workspace(self):
        '''Tests calling ScaleFileManager.download_files() with an inactive workspace'''

        download_dir = os.path.join('download', 'dir')
        work_dir = os.path.join('work', 'dir')

        workspace_1 = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(workspace=workspace_1)
        local_path_1 = u'my/local/path/file.txt'
        file_2 = storage_test_utils.create_file(workspace=workspace_1)
        local_path_2 = u'another/local/path/file.txt'
        file_3 = storage_test_utils.create_file(workspace=workspace_1)
        local_path_3 = u'another/local/path/file.json'
        workspace_1.download_files = MagicMock()
        workspace_1_work_dir = ScaleFile.objects._get_workspace_work_dir(work_dir, workspace_1)

        workspace_2 = storage_test_utils.create_workspace()
        workspace_2.is_active = False
        workspace_2.save()
        file_4 = storage_test_utils.create_file(workspace=workspace_2)
        local_path_4 = u'my/local/path/4/file.txt'
        file_5 = storage_test_utils.create_file(workspace=workspace_2)
        local_path_5 = u'another/local/path/5/file.txt'
        workspace_2_work_dir = ScaleFile.objects._get_workspace_work_dir(work_dir, workspace_2)

        files = [(file_1, local_path_1), (file_2, local_path_2), (file_3, local_path_3), (file_4, local_path_4),
                 (file_5, local_path_5)]
        self.assertRaises(ArchivedWorkspace, ScaleFile.objects.download_files, download_dir, work_dir, files)

    def test_deleted_file(self):
        '''Tests calling ScaleFileManager.download_files() with a deleted file'''

        download_dir = os.path.join('download', 'dir')
        work_dir = os.path.join('work', 'dir')

        workspace_1 = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(workspace=workspace_1)
        local_path_1 = u'my/local/path/file.txt'
        file_2 = storage_test_utils.create_file(workspace=workspace_1)
        local_path_2 = u'another/local/path/file.txt'
        file_2.is_deleted = True
        file_2.save()
        file_3 = storage_test_utils.create_file(workspace=workspace_1)
        local_path_3 = u'another/local/path/file.json'
        workspace_1.download_files = MagicMock()
        workspace_1_work_dir = ScaleFile.objects._get_workspace_work_dir(work_dir, workspace_1)

        workspace_2 = storage_test_utils.create_workspace()
        file_4 = storage_test_utils.create_file(workspace=workspace_2)
        local_path_4 = u'my/local/path/4/file.txt'
        file_5 = storage_test_utils.create_file(workspace=workspace_2)
        local_path_5 = u'another/local/path/5/file.txt'
        workspace_2.download_files = MagicMock()
        workspace_2_work_dir = ScaleFile.objects._get_workspace_work_dir(work_dir, workspace_2)

        files = [(file_1, local_path_1), (file_2, local_path_2), (file_3, local_path_3), (file_4, local_path_4),
                 (file_5, local_path_5)]
        self.assertRaises(DeletedFile, ScaleFile.objects.download_files, download_dir, work_dir, files)


class TestScaleFileManagerGetTotalFileSize(TestCase):

    def setUp(self):
        django.setup()

    def test_success(self):
        '''Tests calling ScaleFileManager.get_total_file_size() successfully'''

        file_1 = storage_test_utils.create_file(file_size=100)
        file_2 = storage_test_utils.create_file(file_size=300)
        storage_test_utils.create_file(file_size=700)

        file_size = ScaleFile.objects.get_total_file_size([file_1.id, file_2.id])
        self.assertEqual(file_size, 400)

    def test_no_files(self):
        '''Tests calling ScaleFileManager.get_total_file_size() where no files match the file IDs'''

        storage_test_utils.create_file(file_size=100)

        file_size = ScaleFile.objects.get_total_file_size([4444444444, 555555555555, 666666666666])
        self.assertEqual(file_size, 0)


class TestScaleFileManagerMoveFiles(TestCase):

    def setUp(self):
        django.setup()

    @patch('storage.models.os.makedirs')
    def test_success(self, mock_makedirs):
        '''Tests calling ScaleFileManager.move_files() successfully'''

        work_dir = os.path.join('work', 'dir')

        workspace_1 = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(file_name='my_file_1.txt', workspace=workspace_1)
        old_path_1 = file_1.file_path
        new_workspace_path_1 = os.path.join('my', 'new', 'path', '1', os.path.basename(file_1.file_path))
        file_2 = storage_test_utils.create_file(file_name='my_file_2.txt', workspace=workspace_1)
        old_path_2 = file_2.file_path
        new_workspace_path_2 = os.path.join('my', 'new', 'path', '2', os.path.basename(file_2.file_path))
        workspace_1.move_files = MagicMock()
        workspace_1_work_dir = ScaleFile.objects._get_workspace_work_dir(work_dir, workspace_1)

        workspace_2 = storage_test_utils.create_workspace()
        file_3 = storage_test_utils.create_file(file_name='my_file_3.txt', workspace=workspace_2)
        old_path_3 = file_3.file_path
        new_workspace_path_3 = os.path.join('my', 'new', 'path', '3', os.path.basename(file_3.file_path))
        file_4 = storage_test_utils.create_file(file_name='my_file_4.txt', workspace=workspace_2)
        old_path_4 = file_4.file_path
        new_workspace_path_4 = os.path.join('my', 'new', 'path', '4', os.path.basename(file_4.file_path))
        workspace_2.move_files = MagicMock()
        workspace_2_work_dir = ScaleFile.objects._get_workspace_work_dir(work_dir, workspace_2)

        files = [(file_1, new_workspace_path_1), (file_2, new_workspace_path_2), (file_3, new_workspace_path_3),
                 (file_4, new_workspace_path_4)]
        ScaleFile.objects.move_files(work_dir, files)

        workspace_1.move_files.assert_called_once_with(workspace_1_work_dir,
                                                       [(old_path_1, new_workspace_path_1),
                                                        (old_path_2, new_workspace_path_2)])
        workspace_2.move_files.assert_called_once_with(workspace_2_work_dir,
                                                       [(old_path_3, new_workspace_path_3),
                                                        (old_path_4, new_workspace_path_4)])
        # Check models for new workspace paths
        new_file_1 = ScaleFile.objects.get(id=file_1.id)
        self.assertEqual(new_file_1.file_path, new_workspace_path_1)
        new_file_2 = ScaleFile.objects.get(id=file_2.id)
        self.assertEqual(new_file_2.file_path, new_workspace_path_2)
        new_file_3 = ScaleFile.objects.get(id=file_3.id)
        self.assertEqual(new_file_3.file_path, new_workspace_path_3)
        new_file_4 = ScaleFile.objects.get(id=file_4.id)
        self.assertEqual(new_file_4.file_path, new_workspace_path_4)

    def test_inactive_workspace(self):
        '''Tests calling ScaleFileManager.move_files() with an inactive workspace'''

        work_dir = os.path.join('work', 'dir')

        workspace_1 = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(file_name='my_file_1.txt', workspace=workspace_1)
        new_workspace_path_1 = os.path.join('my', 'new', 'path', '1', os.path.basename(file_1.file_path))
        file_2 = storage_test_utils.create_file(file_name='my_file_2.txt', workspace=workspace_1)
        new_workspace_path_2 = os.path.join('my', 'new', 'path', '2', os.path.basename(file_2.file_path))
        workspace_1.move_files = MagicMock()
        workspace_1_work_dir = ScaleFile.objects._get_workspace_work_dir(work_dir, workspace_1)

        workspace_2 = storage_test_utils.create_workspace()
        workspace_2.is_active = False
        workspace_2.save()
        file_3 = storage_test_utils.create_file(file_name='my_file_3.txt', workspace=workspace_2)
        new_workspace_path_3 = os.path.join('my', 'new', 'path', '3', os.path.basename(file_3.file_path))
        file_4 = storage_test_utils.create_file(file_name='my_file_4.txt', workspace=workspace_2)
        new_workspace_path_4 = os.path.join('my', 'new', 'path', '4', os.path.basename(file_4.file_path))
        workspace_2.move_files = MagicMock()
        workspace_2_work_dir = ScaleFile.objects._get_workspace_work_dir(work_dir, workspace_2)

        files = [(file_1, new_workspace_path_1), (file_2, new_workspace_path_2), (file_3, new_workspace_path_3),
                 (file_4, new_workspace_path_4)]
        self.assertRaises(ArchivedWorkspace, ScaleFile.objects.move_files, work_dir, files)

    def test_deleted_file(self):
        '''Tests calling ScaleFileManager.move_files() with a deleted file'''

        work_dir = os.path.join('work', 'dir')

        workspace_1 = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(file_name='my_file_1.txt', workspace=workspace_1)
        new_workspace_path_1 = os.path.join('my', 'new', 'path', '1', os.path.basename(file_1.file_path))
        file_2 = storage_test_utils.create_file(file_name='my_file_2.txt', workspace=workspace_1)
        file_2.is_deleted = True
        file_2.save()
        new_workspace_path_2 = os.path.join('my', 'new', 'path', '2', os.path.basename(file_2.file_path))
        workspace_1.move_files = MagicMock()
        workspace_1_work_dir = ScaleFile.objects._get_workspace_work_dir(work_dir, workspace_1)

        workspace_2 = storage_test_utils.create_workspace()
        workspace_2.is_active = False
        workspace_2.save()
        file_3 = storage_test_utils.create_file(file_name='my_file_3.txt', workspace=workspace_2)
        new_workspace_path_3 = os.path.join('my', 'new', 'path', '3', os.path.basename(file_3.file_path))
        file_4 = storage_test_utils.create_file(file_name='my_file_4.txt', workspace=workspace_2)
        new_workspace_path_4 = os.path.join('my', 'new', 'path', '4', os.path.basename(file_4.file_path))
        workspace_2.move_files = MagicMock()
        workspace_2_work_dir = ScaleFile.objects._get_workspace_work_dir(work_dir, workspace_2)

        files = [(file_1, new_workspace_path_1), (file_2, new_workspace_path_2), (file_3, new_workspace_path_3),
                 (file_4, new_workspace_path_4)]
        self.assertRaises(DeletedFile, ScaleFile.objects.move_files, work_dir, files)


class TestScaleFileManagerSetupUploadDir(TestCase):

    def setUp(self):
        django.setup()

    @patch('storage.models.os.makedirs')
    def test_success(self, mock_makedirs):
        '''Tests calling ScaleFileManager.setup_upload_dir() successfully'''

        upload_dir = os.path.join('upload', 'dir')
        work_dir = os.path.join('work', 'dir')

        workspace_1 = storage_test_utils.create_workspace()
        workspace_1.setup_upload_dir = MagicMock()
        workspace_1_work_dir = ScaleFile.objects._get_workspace_work_dir(work_dir, workspace_1)

        ScaleFile.objects.setup_upload_dir(upload_dir, work_dir, workspace_1)

        workspace_1.setup_upload_dir.assert_called_once_with(upload_dir, workspace_1_work_dir)


class TestScaleFileManagerUploadFiles(TestCase):

    def setUp(self):
        django.setup()

    @patch('storage.models.os.path.getsize')
    def test_success(self, mock_getsize):
        '''Tests calling ScaleFileManager.upload_files() successfully'''
        def new_getsize(path):
            return 100
        mock_getsize.side_effect = new_getsize

        upload_dir = os.path.join('upload', 'dir')
        work_dir = os.path.join('work', 'dir')

        workspace = storage_test_utils.create_workspace()
        file_1 = ScaleFile()
        file_1.media_type = None  # Scale should auto-detect text/plain
        remote_path_1 = u'my/remote/path/file.txt'
        local_path_1 = u'my/local/path/file.txt'
        file_2 = ScaleFile()
        file_2.media_type = u'application/json'
        remote_path_2 = u'my/remote/path/2/file.json'
        local_path_2 = u'my/local/path/2/file.json'
        workspace.upload_files = MagicMock()
        workspace.delete_files = MagicMock()
        workspace_work_dir = ScaleFile.objects._get_workspace_work_dir(work_dir, workspace)

        files = [(file_1, local_path_1, remote_path_1), (file_2, local_path_2, remote_path_2)]
        models = ScaleFile.objects.upload_files(upload_dir, work_dir, workspace, files)

        workspace.upload_files.assert_called_once_with(upload_dir, workspace_work_dir,
                                                       [(local_path_1, remote_path_1), (local_path_2, remote_path_2)])
        self.assertListEqual(workspace.delete_files.call_args_list, [])

        self.assertEqual(u'file.txt', models[0].file_name)
        self.assertEqual(remote_path_1, models[0].file_path)
        self.assertEqual(u'text/plain', models[0].media_type)
        self.assertEqual(workspace.id, models[0].workspace_id)
        self.assertEqual(u'file.json', models[1].file_name)
        self.assertEqual(remote_path_2, models[1].file_path)
        self.assertEqual(u'application/json', models[1].media_type)
        self.assertEqual(workspace.id, models[1].workspace_id)

    @patch('storage.models.os.path.getsize')
    @patch('storage.models.os.makedirs')
    def test_fails(self, mock_makedirs, mock_getsize):
        '''Tests calling ScaleFileManager.upload_files() when Workspace.upload_files() fails'''
        def new_getsize(path):
            return 100
        mock_getsize.side_effect = new_getsize

        upload_dir = os.path.join('upload', 'dir')
        work_dir = os.path.join('work', 'dir')

        workspace = storage_test_utils.create_workspace()
        file_1 = ScaleFile()
        file_1.media_type = None  # Scale should auto-detect text/plain
        remote_path_1 = u'my/remote/path/file.txt'
        local_path_1 = u'my/local/path/file.txt'
        file_2 = ScaleFile()
        file_2.media_type = u'application/json'
        remote_path_2 = u'my/remote/path/2/file.json'
        local_path_2 = u'my/local/path/2/file.json'
        workspace.upload_files = MagicMock()
        workspace.upload_files.side_effect = Exception
        workspace.delete_files = MagicMock()
        delete_work_dir = os.path.join(work_dir, 'delete', get_valid_filename(workspace.name))

        files = [(file_1, local_path_1, remote_path_1), (file_2, local_path_2, remote_path_2)]
        self.assertRaises(Exception, ScaleFile.objects.upload_files, upload_dir, work_dir, workspace, files)
        # Make sure the files get cleaned up
        workspace.delete_files.assert_called_once_with(delete_work_dir, [remote_path_1, remote_path_2])


class TestScaleFile(TestCase):

    def setUp(self):
        django.setup()

    def test_url(self):
        '''Tests building a URL for a file.'''
        ws = storage_test_utils.create_workspace(name='test', base_url='http://localhost') 
        file = storage_test_utils.create_file(file_name='test.txt', workspace=ws)

        self.assertEqual(file.url, 'http://localhost/file/path/test.txt')

    def test_url_base_url_missing(self):
        '''Tests building a URL for a file in a workspace with no configured base URL.'''
        ws = storage_test_utils.create_workspace(name='test') 
        file = storage_test_utils.create_file(file_name='test.txt', workspace=ws)

        self.assertIsNone(file.url)

    def test_url_base_slash(self):
        '''Tests building a URL for a file where the workspace base URL has a trailing slash.'''
        ws = storage_test_utils.create_workspace(name='test', base_url='http://localhost/') 
        file = storage_test_utils.create_file(file_name='test.txt', workspace=ws)

        self.assertEqual(file.url, 'http://localhost/file/path/test.txt')

    def test_url_file_slash(self):
        '''Tests building a URL for a file where the file path URL has a leading slash.'''
        ws = storage_test_utils.create_workspace(name='test', base_url='http://localhost') 
        file = storage_test_utils.create_file(file_name='test.txt', file_path='/file/path/test.txt',
                                                          workspace=ws)

        self.assertEqual(file.url, 'http://localhost/file/path/test.txt')
    
    def test_country_data(self):
        '''Tests adding a border and country intersection calculation.'''
        testborder = geos.Polygon(((0, 0), (0, 10), (10, 10), (10, 0), (0, 0)))
        testborder2 = geos.Polygon(((11, 0), (11, 8), (19, 8), (19, 0), (11, 0)))
        testborder3 = geos.Polygon(((11, 11), (11, 15), (15, 15), (15, 11), (11, 11)))
        testeffective = datetime.datetime(2000, 1, 1, 0, 0, 0, tzinfo=utc)
        CountryData.objects.create(name="Test Country", fips="TC", gmi="TCY", iso2="TC", iso3="TCY", iso_num=42,
                                   border=testborder, effective=testeffective)
        CountryData.objects.create(name="Test Country 2", fips="TT", gmi="TCT", iso2="TT", iso3="TCT", iso_num=43,
                                   border=testborder2, effective=testeffective)
        CountryData.objects.create(name="Test Country 3", fips="TH", gmi="TCH", iso2="TH", iso3="TCH", iso_num=44,
                                   border=testborder3, effective=testeffective)
        ws = storage_test_utils.create_workspace(name='test', base_url='http://localhost') 
        file = storage_test_utils.create_file(file_name='test.txt', workspace=ws)
        with transaction.atomic():
            file.geometry = geos.Polygon(((5, 5), (5, 10), (12, 10), (12, 5), (5, 5)))
            file.set_countries()
            file.save()
        tmp = [c.iso2 for c in file.countries.all()]
        self.assertEqual(len(tmp), 2)
        self.assertIn("TC", tmp)
        self.assertIn("TT", tmp)


class TestCountryData(TestCase):

    def setUp(self):
        django.setup()
        self.testborder = geos.Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0)))
        self.testeffective = datetime.datetime(2000, 1, 1, 0, 0, 0, tzinfo=utc)
        CountryData.objects.create(name="Test Country", fips="TC", gmi="TCY", iso2="TC", iso3="TCY", iso_num=42,
                                   border=self.testborder, effective=self.testeffective)

    def test_access(self):
        tmp = CountryData.objects.filter(name="Test Country")
        self.assertEqual(tmp.count(), 1)
        self.assertEqual(tmp[0].fips, "TC")
        self.assertEqual(tmp[0].gmi, "TCY")
        self.assertEqual(tmp[0].iso2, "TC")
        self.assertEqual(tmp[0].iso3, "TCY")
        self.assertEqual(tmp[0].iso_num, 42)
        self.assertEqual(tmp[0].border, self.testborder)
        self.assertEqual(tmp[0].effective, self.testeffective)
    
    def test_not_found(self):
        tmp = CountryData.objects.filter(name="Kerblekistan")
        self.assertEqual(tmp.count(), 0)
    
    def test_border_update(self):
        newborder = geos.Polygon(((0, 0), (42, 0), (42, 42), (0, 42), (0, 0)))
        neweffective = datetime.datetime(2010, 4, 5, 18, 26, 0, tzinfo=utc)
        CountryData.objects.update_border("Test Country", newborder, neweffective)
        tmp = CountryData.objects.filter(name="Test Country", effective=neweffective)
        self.assertEqual(tmp[0].border, newborder)
        self.assertEqual(tmp[0].effective, neweffective)
        self.assertEqual(tmp[0].fips, "TC")

    def test_border_update_not_found(self):
        newborder = geos.Polygon(((0, 0), (42, 0), (42, 42), (0, 42), (0, 0)))
        self.assertRaises(CountryData.DoesNotExist, CountryData.objects.update_border, "Kerblekistan", newborder)
