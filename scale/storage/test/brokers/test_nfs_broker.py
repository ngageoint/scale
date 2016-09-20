from __future__ import unicode_literals

import os

import django
from django.test import TestCase
from mock import call, patch, mock_open

import storage.test.utils as storage_test_utils
from storage.brokers.broker import FileDownload, FileMove, FileUpload
from storage.brokers.exceptions import InvalidBrokerConfiguration
from storage.brokers.nfs_broker import NfsBroker


class TestNfsBrokerDeleteFiles(TestCase):

    def setUp(self):
        django.setup()

        self.broker = NfsBroker()
        self.broker.load_configuration({'type': NfsBroker().broker_type, 'nfs_path': 'host:/path'})

    @patch('storage.brokers.nfs_broker.os.path.exists')
    @patch('storage.brokers.nfs_broker.os.remove')
    def test_successfully(self, mock_remove, mock_exists):
        """Tests calling NfsBroker.delete_files() successfully"""

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


class TestNfsBrokerDownloadFiles(TestCase):

    def setUp(self):
        django.setup()

        self.broker = NfsBroker()
        self.broker.load_configuration({'type': NfsBroker().broker_type, 'nfs_path': 'host:/path'})

    @patch('storage.brokers.nfs_broker.os.path.exists')
    @patch('storage.brokers.nfs_broker.execute_command_line')
    def test_successfully(self, mock_execute, mock_exists):
        """Tests calling NfsBroker.download_files() successfully"""

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
        file_1_dl = FileDownload(file_1, local_path_file_1, False)
        file_2_dl = FileDownload(file_2, local_path_file_2, False)

        # Call method to test
        self.broker.download_files(volume_path, [file_1_dl, file_2_dl])

        # Check results
        two_calls = [call(['ln', '-s', full_workspace_path_file_1, local_path_file_1]),
                     call(['ln', '-s', full_workspace_path_file_2, local_path_file_2])]
        mock_execute.assert_has_calls(two_calls)


class TestNfsBrokerLoadConfiguration(TestCase):

    def setUp(self):
        django.setup()

    def test_successfully(self):
        """Tests calling NfsBroker.load_configuration() successfully"""

        nfs_path = 'host:/dir'

        # Call method to test
        broker = NfsBroker()
        broker.load_configuration({'type': NfsBroker().broker_type, 'nfs_path': nfs_path})

        volume = broker.volume
        self.assertEqual(volume.driver, 'nfs')
        self.assertEqual(volume.host, False)
        self.assertEqual(volume.remote_path, 'host/dir')  # No : character in path for Docker NFS volume


class TestNfsBrokerMoveFiles(TestCase):

    def setUp(self):
        django.setup()

        self.broker = NfsBroker()
        self.broker.load_configuration({'type': NfsBroker().broker_type, 'nfs_path': 'host:/path'})

    @patch('storage.brokers.nfs_broker.os.makedirs')
    @patch('storage.brokers.nfs_broker.os.path.exists')
    @patch('storage.brokers.nfs_broker.os.chmod')
    @patch('storage.brokers.nfs_broker.shutil.move')
    def test_successfully(self, mock_move, mock_chmod, mock_exists, mock_makedirs):
        """Tests calling NfsBroker.move_files() successfully"""

        def new_exists(path):
            return False
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


class TestNfsBrokerUploadFiles(TestCase):

    def setUp(self):
        django.setup()

        self.broker = NfsBroker()
        self.broker.load_configuration({'type': NfsBroker().broker_type, 'nfs_path': 'host:/path'})

    @patch('storage.brokers.nfs_broker.os.makedirs')
    @patch('storage.brokers.nfs_broker.os.path.exists')
    @patch('storage.brokers.nfs_broker.os.chmod')
    @patch('storage.brokers.nfs_broker.shutil.copy')
    def test_successfully(self, mock_copy, mock_chmod, mock_exists, mock_makedirs):
        """Tests calling NfsBroker.upload_files() successfully"""

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
        mountstats_data = """16 36 0:3 / /proc rw,nosuid,nodev,noexec,relatime shared:5 - proc proc rw
17 36 0:16 / /sys rw,nosuid,nodev,noexec,relatime shared:6 - sysfs sysfs rw
18 36 0:5 / /dev rw,nosuid shared:2 - devtmpfs devtmpfs rw,size=32977500k,nr_inodes=8244375,mode=755
19 17 0:15 / /sys/kernel/security rw,nosuid,nodev,noexec,relatime shared:7 - securityfs securityfs rw
20 18 0:17 / /dev/shm rw,nosuid,nodev shared:3 - tmpfs tmpfs rw
21 18 0:11 / /dev/pts rw,nosuid,noexec,relatime shared:4 - devpts devpts rw,gid=5,mode=620,ptmxmode=000
22 36 0:18 / /run rw,nosuid,nodev shared:21 - tmpfs tmpfs rw,mode=755
23 17 0:19 / /sys/fs/cgroup rw,nosuid,nodev,noexec shared:8 - tmpfs tmpfs rw,mode=755
24 23 0:20 / /sys/fs/cgroup/systemd rw,nosuid,nodev,noexec,relatime shared:9 - cgroup cgroup rw,xattr,release_agent=/usr/lib/systemd/systemd-cgroups-agent,name=systemd
25 17 0:21 / /sys/fs/pstore rw,nosuid,nodev,noexec,relatime shared:19 - pstore pstore rw
26 23 0:22 / /sys/fs/cgroup/cpuset rw,nosuid,nodev,noexec,relatime shared:10 - cgroup cgroup rw,cpuset
27 23 0:23 / /sys/fs/cgroup/cpu,cpuacct rw,nosuid,nodev,noexec,relatime shared:11 - cgroup cgroup rw,cpu,cpuacct
28 23 0:24 / /sys/fs/cgroup/memory rw,nosuid,nodev,noexec,relatime shared:12 - cgroup cgroup rw,memory
29 23 0:25 / /sys/fs/cgroup/devices rw,nosuid,nodev,noexec,relatime shared:13 - cgroup cgroup rw,devices
30 23 0:26 / /sys/fs/cgroup/freezer rw,nosuid,nodev,noexec,relatime shared:14 - cgroup cgroup rw,freezer
31 23 0:27 / /sys/fs/cgroup/net_cls,net_prio rw,nosuid,nodev,noexec,relatime shared:15 - cgroup cgroup rw,net_cls,net_prio
32 23 0:28 / /sys/fs/cgroup/blkio rw,nosuid,nodev,noexec,relatime shared:16 - cgroup cgroup rw,blkio
33 23 0:29 / /sys/fs/cgroup/perf_event rw,nosuid,nodev,noexec,relatime shared:17 - cgroup cgroup rw,perf_event
34 23 0:30 / /sys/fs/cgroup/hugetlb rw,nosuid,nodev,noexec,relatime shared:18 - cgroup cgroup rw,hugetlb
35 17 0:31 / /sys/kernel/config rw,relatime shared:20 - configfs configfs rw
36 0 253:0 / / rw,relatime shared:1 - xfs /dev/mapper/vg_root-lv_root rw,attr2,inode64,noquota
14 36 0:14 / /users rw,relatime shared:22 - autofs systemd-1 rw,fd=29,pgrp=1,timeout=300,minproto=5,maxproto=5,direct
39 16 0:34 / /proc/sys/fs/binfmt_misc rw,relatime shared:25 - autofs systemd-1 rw,fd=37,pgrp=1,timeout=300,minproto=5,maxproto=5,direct
41 18 0:13 / /dev/mqueue rw,relatime shared:26 - mqueue mqueue rw
40 17 0:6 / /sys/kernel/debug rw,relatime shared:27 - debugfs debugfs rw
42 18 0:35 / /dev/hugepages rw,relatime shared:28 - hugetlbfs hugetlbfs rw
43 36 0:36 / /var/lib/nfs/rpc_pipefs rw,relatime shared:29 - rpc_pipefs sunrpc rw
44 16 0:37 / /proc/fs/nfsd rw,relatime shared:30 - nfsd nfsd rw
45 36 8:2 / /boot rw,relatime shared:31 - xfs /dev/sda2 rw,attr2,inode64,noquota
46 14 0:40 / /users rw,relatime shared:32 - nfs4 users:/users rw,vers=4.0,rsize=1048576,wsize=1048576,namlen=255,hard,proto=tcp,port=0,timeo=14,retrans=2,sec=sys,local_lock=none
49 39 0:38 / /proc/sys/fs/binfmt_misc rw,relatime shared:35 - binfmt_misc binfmt_misc rw
48 38 0:42 / %s rw,relatime shared:34 - nfs4 fserver:/exports/my_dir_1 rw,vers=4.0,rsize=1048576,wsize=1048576,namlen=255,hard,proto=tcp,port=0,timeo=14,retrans=2,sec=sys,local_lock=none
""" % (os.path.abspath(volume_path),)
        mo = mock_open(read_data=mountstats_data)
        # need to patch readlines() since only read() is patched in mock_open
        mo.return_value.readlines.return_value = mo.return_value.read.return_value.split('\n')
        with patch('__builtin__.open', mo, create=True) as pmo:
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


class TestNfsBrokerValidateConfiguration(TestCase):

    def setUp(self):
        django.setup()

    def test_successfully(self):
        """Tests calling NfsBroker.validate_configuration() successfully"""

        nfs_path = 'host:/dir'

        # Call method to test
        broker = NfsBroker()
        # No exception is success
        broker.validate_configuration({'type': NfsBroker().broker_type, 'nfs_path': nfs_path})

    def test_missing_nfs_path(self):
        """Tests calling NfsBroker.validate_configuration() with a missing nfs_path value"""

        # Call method to test
        broker = NfsBroker()
        self.assertRaises(InvalidBrokerConfiguration, broker.validate_configuration,
                          {'type': NfsBroker().broker_type})
