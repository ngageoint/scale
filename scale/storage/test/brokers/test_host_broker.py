from __future__ import unicode_literals

import os
import shutil
import tempfile
import uuid

import django
from django.test import TestCase
from mock import call, patch

import storage.test.utils as storage_test_utils
from storage.brokers.broker import FileDownload, FileMove, FileUpload
from storage.brokers.exceptions import InvalidBrokerConfiguration
from storage.brokers.host_broker import HostBroker


class TestHostBrokerDeleteFiles(TestCase):

    def setUp(self):
        django.setup()

        self.broker = HostBroker()
        self.broker.load_configuration({'type': HostBroker().broker_type, 'host_path': '/host/path'})

    @patch('storage.brokers.host_broker.os.path.exists')
    @patch('storage.brokers.host_broker.os.remove')
    def test_successfully(self, mock_remove, mock_exists):
        """Tests calling HostBroker.delete_files() successfully"""

        def new_exists(path):
            return True
        mock_exists.side_effect = new_exists

        volume_path = os.path.join('the', 'volume', 'path')
        file_path_1 = os.path.join('my_dir', 'my_file.txt')
        file_path_2 = os.path.join('my_dir', 'my_file.json')
        full_path_file_1 = os.path.join(volume_path, file_path_1)
        full_path_file_2 = os.path.join(volume_path, file_path_2)

        file_1 = storage_test_utils.create_file(file_path=file_path_1)
        file_2 = storage_test_utils.create_file(file_path=file_path_2)

        # Call method to test
        self.broker.delete_files(volume_path, [file_1, file_2])

        # Check results
        two_calls = [call(full_path_file_1), call(full_path_file_2)]
        mock_remove.assert_has_calls(two_calls)

        self.assertTrue(file_1.is_deleted)
        self.assertIsNotNone(file_1.deleted)
        self.assertTrue(file_2.is_deleted)
        self.assertIsNotNone(file_2.deleted)


class TestHostBrokerDownloadFiles(TestCase):

    def setUp(self):
        django.setup()

        self.broker = HostBroker()
        self.broker.load_configuration({'type': HostBroker().broker_type, 'host_path': '/host/path'})

    @patch('storage.brokers.host_broker.os.path.exists')
    @patch('storage.brokers.host_broker.execute_command_line')
    def test_successfully(self, mock_execute, mock_exists):
        """Tests calling HostBroker.download_files() successfully"""

        mock_exists.return_value = True

        volume_path = os.path.join('the', 'volume', 'path')
        file_name_1 = 'my_file.txt'
        file_name_2 = 'my_file.json'
        local_path_file_1 = os.path.join('my_dir_1', file_name_1)
        local_path_file_2 = os.path.join('my_dir_2', file_name_2)
        workspace_path_file_1 = os.path.join('my_wrk_dir_1', file_name_1)
        workspace_path_file_2 = os.path.join('my_wrk_dir_2', file_name_2)
        full_workspace_path_file_1 = os.path.join(volume_path, workspace_path_file_1)
        full_workspace_path_file_2 = os.path.join(volume_path, workspace_path_file_2)

        file_1 = storage_test_utils.create_file(file_path=workspace_path_file_1)
        file_2 = storage_test_utils.create_file(file_path=workspace_path_file_2)
        file_1_dl = FileDownload(file_1, local_path_file_1, False)
        file_2_dl = FileDownload(file_2, local_path_file_2, False)

        # Call method to test
        self.broker.download_files(volume_path, [file_1_dl, file_2_dl])

        # Check results
        two_calls = [call(['ln', '-s', full_workspace_path_file_1, local_path_file_1]),
                     call(['ln', '-s', full_workspace_path_file_2, local_path_file_2])]
        mock_execute.assert_has_calls(two_calls)


class TestHostBrokerListFiles(TestCase):

    def setUp(self):
        django.setup()
        
        self.root_path = '/my/test/path'
        self.broker = HostBroker()

    @patch('os.listdir')
    def test_no_files_flat_walk(self, list_dir):
        """Tests calling HostBroker._dir_walker() with no files in directory"""
        
        file_list = [x for x in HostBroker._dir_walker(self.root_path, False)]
        
        self.assertEqual(len(file_list), 0)

    @patch('os.listdir')
    def test_with_files_flat_dir_walker(self, list_dir):
        """Tests calling HostBroker._dir_walker() with files in a directory"""
        
        files = [str(uuid.uuid4()), str(uuid.uuid4())]

        list_dir.return_value = files
        
        file_list = [x for x in HostBroker._dir_walker(self.root_path, False)]

        for i in range(2):
            self.assertEqual(os.path.join(self.root_path, files[i]), file_list[i])
            
        self.assertEqual(len(file_list), 2)

    @patch('os.walk')
    def test_with_files_recursive_dir_walker(self, walk):
        """Tests calling HostBroker._dir_walker() with files throughout tree"""
        
        files = []
        dirs = {self.root_path: str(uuid.uuid4()),
                os.path.join(self.root_path, str(uuid.uuid4())): str(uuid.uuid4()),
                os.path.join(self.root_path, str(uuid.uuid4())): str(uuid.uuid4())}

        files = [os.path.join(x, dirs[x]) for x in dirs]

        walk.return_value = [(x, (), (dirs[x],)) for x in dirs]
        
        file_list = [x for x in HostBroker._dir_walker(self.root_path, True)]
        
        for i in range(3):
            self.assertEqual(os.path.join(self.root_path, files[i]), file_list[i])
        self.assertEqual(len(file_list), 3)

    @patch('storage.brokers.host_broker.HostBroker._dir_walker')
    def test_no_files(self, walk):
        """Tests calling HostBroker.list_files() with no files in directory"""
        
        walk.return_value = []
        files = self.broker.list_files(self.root_path, False)
        self.assertEqual(len(list(files)), 0)
    
    @patch('os.path.getsize', lambda x: 0)
    @patch('os.path.isfile', lambda x: True)
    @patch('storage.brokers.host_broker.HostBroker._dir_walker')
    def test_list_a_thousand(self, walk):
        """Tests calling HostBroker.list_files() with multiple batches (1000+)"""
        
        walk.return_value = [str(uuid.uuid4()) for _ in range(1500)]
        
        files = self.broker.list_files(self.root_path, True)
        
        self.assertEqual(len(list(files)), 1500)
    
    @patch('os.path.getsize', lambda x: 0)
    @patch('os.path.isfile', lambda x: True)
    @patch('storage.brokers.host_broker.HostBroker._dir_walker')
    def test_list_ten(self, walk):
        """Tests calling HostBroker.list_files() to search directory"""
        
        walk.return_value = [str(uuid.uuid4()) for _ in range(10)]
        
        files = self.broker.list_files(self.root_path, True)
        
        self.assertEqual(len(list(files)), 10)
    
    @patch('os.path.getsize', lambda x: 0)
    @patch('os.path.isfile', lambda x: True)
    @patch('storage.brokers.host_broker.HostBroker._dir_walker')
    def test_recursive_successfully(self, walk):
        """Tests calling HostBroker.list_files() with files across multi-level 
        directory tree"""
        
        walk.return_value = [os.path.join(str(x), str(uuid.uuid4())) for x in range(10)]

        files = self.broker.list_files(self.root_path, True)
        
        self.assertEqual(len(list(files)), 10)


class TestHostBrokerLoadConfiguration(TestCase):

    def setUp(self):
        django.setup()

    def test_successfully(self):
        """Tests calling HostBroker.load_configuration() successfully"""

        host_path = '/host/path'

        # Call method to test
        broker = HostBroker()
        broker.load_configuration({'type': HostBroker().broker_type, 'host_path': host_path})

        volume = broker.volume
        self.assertEqual(volume.driver, None)
        self.assertEqual(volume.host, True)
        self.assertEqual(volume.remote_path, host_path)


class TestHostBrokerMoveFiles(TestCase):

    def setUp(self):
        django.setup()

        self.broker = HostBroker()
        self.broker.load_configuration({'type': HostBroker().broker_type, 'host_path': '/host/path'})

    @patch('storage.brokers.host_broker.os.makedirs')
    @patch('storage.brokers.host_broker.os.path.exists')
    @patch('storage.brokers.host_broker.os.chmod')
    @patch('storage.brokers.host_broker.shutil.move')
    def test_successfully(self, mock_move, mock_chmod, mock_exists, mock_makedirs):
        """Tests calling HostBroker.move_files() successfully"""

        def new_exists(path):
            return path.count('new') == 0
        mock_exists.side_effect = new_exists

        volume_path = os.path.join('the', 'volume', 'path')
        file_name_1 = 'my_file.txt'
        file_name_2 = 'my_file.json'
        old_workspace_path_1 = os.path.join('my_dir_1', file_name_1)
        old_workspace_path_2 = os.path.join('my_dir_2', file_name_2)
        new_workspace_path_1 = os.path.join('my_new_dir_1', file_name_1)
        new_workspace_path_2 = os.path.join('my_new_dir_2', file_name_2)
        full_old_workspace_path_1 = os.path.join(volume_path, old_workspace_path_1)
        full_old_workspace_path_2 = os.path.join(volume_path, old_workspace_path_2)
        full_new_workspace_path_1 = os.path.join(volume_path, new_workspace_path_1)
        full_new_workspace_path_2 = os.path.join(volume_path, new_workspace_path_2)

        file_1 = storage_test_utils.create_file(file_path=old_workspace_path_1)
        file_2 = storage_test_utils.create_file(file_path=old_workspace_path_2)
        file_1_mv = FileMove(file_1, new_workspace_path_1)
        file_2_mv = FileMove(file_2, new_workspace_path_2)

        # Call method to test
        self.broker.move_files(volume_path, [file_1_mv, file_2_mv])

        # Check results
        two_calls = [call(os.path.dirname(full_new_workspace_path_1), mode=0755),
                     call(os.path.dirname(full_new_workspace_path_2), mode=0755)]
        mock_makedirs.assert_has_calls(two_calls)
        two_calls = [call(full_old_workspace_path_1, full_new_workspace_path_1),
                     call(full_old_workspace_path_2, full_new_workspace_path_2)]
        mock_move.assert_has_calls(two_calls)
        two_calls = [call(full_new_workspace_path_1, 0644), call(full_new_workspace_path_2, 0644)]
        mock_chmod.assert_has_calls(two_calls)

        self.assertEqual(file_1.file_path, new_workspace_path_1)
        self.assertEqual(file_2.file_path, new_workspace_path_2)


class TestHostBrokerUploadFiles(TestCase):

    def setUp(self):
        django.setup()

        self.broker = HostBroker()
        self.broker.load_configuration({'type': HostBroker().broker_type, 'host_path': '/host/path'})

    @patch('storage.brokers.host_broker.os.makedirs')
    @patch('storage.brokers.host_broker.os.path.exists')
    @patch('storage.brokers.host_broker.os.chmod')
    @patch('storage.brokers.host_broker.shutil.copy')
    def test_successfully(self, mock_copy, mock_chmod, mock_exists, mock_makedirs):
        """Tests calling HostBroker.upload_files() successfully"""

        def new_exists(path):
            return False
        mock_exists.side_effect = new_exists

        volume_path = os.path.join('the', 'volume', 'path')
        file_name_1 = 'my_file.txt'
        file_name_2 = 'my_file.json'
        local_path_file_1 = os.path.join('my_dir_1', file_name_1)
        local_path_file_2 = os.path.join('my_dir_2', file_name_2)
        workspace_path_file_1 = os.path.join('my_wrk_dir_1', file_name_1)
        workspace_path_file_2 = os.path.join('my_wrk_dir_2', file_name_2)
        full_workspace_path_file_1 = os.path.join(volume_path, workspace_path_file_1)
        full_workspace_path_file_2 = os.path.join(volume_path, workspace_path_file_2)

        file_1 = storage_test_utils.create_file(file_path=workspace_path_file_1)
        file_2 = storage_test_utils.create_file(file_path=workspace_path_file_2)
        file_1_up = FileUpload(file_1, local_path_file_1)
        file_2_up = FileUpload(file_2, local_path_file_2)

        # Call method to test
        self.broker.upload_files(volume_path, [file_1_up, file_2_up])

        # Check results
        two_calls = [call(os.path.dirname(full_workspace_path_file_1), mode=0755),
                     call(os.path.dirname(full_workspace_path_file_2), mode=0755)]
        mock_makedirs.assert_has_calls(two_calls)
        two_calls = [call(local_path_file_1, full_workspace_path_file_1),
                     call(local_path_file_2, full_workspace_path_file_2)]
        mock_copy.assert_has_calls(two_calls)
        two_calls = [call(full_workspace_path_file_1, 0644), call(full_workspace_path_file_2, 0644)]
        mock_chmod.assert_has_calls(two_calls)


class TestHostBrokerValidateConfiguration(TestCase):

    def setUp(self):
        django.setup()

    def test_successfully(self):
        """Tests calling HostBroker.validate_configuration() successfully"""

        host_path = 'host:/dir'

        # Call method to test
        broker = HostBroker()
        # No exception is success
        broker.validate_configuration({'type': HostBroker().broker_type, 'host_path': host_path})

    def test_missing_host_path(self):
        """Tests calling HostBroker.validate_configuration() with a missing host_path value"""

        # Call method to test
        broker = HostBroker()
        self.assertRaises(InvalidBrokerConfiguration, broker.validate_configuration,
                          {'type': HostBroker().broker_type})
