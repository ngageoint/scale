#@PydevCodeAnalysisIgnore
import os

import django
from django.test import TestCase
from mock import call, patch, mock_open
from StringIO import StringIO
import sys
import os
import tempfile
from unittest.case import skipIf

from storage.brokers.nfs_broker import NfsBroker
from storage.nfs import nfs_umount


class TestNfsBrokerCleanupDownloadDir(TestCase):

    def setUp(self):
        django.setup()

    @patch('storage.brokers.nfs_broker.os.path.exists')
    @patch('storage.brokers.nfs_broker.nfs_umount')
    def test_successfully(self, mock_umount, mock_exists):
        '''Tests calling NfsBroker.cleanup_download_dir() successfully'''

        def new_exists(path):
            return True
        mock_exists.side_effect = new_exists

        download_dir = os.path.join('the', 'download', 'dir')
        work_dir = os.path.join('the', 'work', 'dir')

        # Call method to test
        broker = NfsBroker()
        broker.cleanup_download_dir(download_dir, work_dir)

        # Check results
        mock_umount.assert_called_once_with(work_dir)


class TestNfsBrokerCleanupUploadDir(TestCase):

    def setUp(self):
        django.setup()

    @patch('storage.brokers.nfs_broker.os.path.exists')
    @patch('storage.brokers.nfs_broker.nfs_umount')
    def test_successfully(self, mock_umount, mock_exists):
        '''Tests calling NfsBroker.cleanup_upload_dir() successfully'''

        def new_exists(path):
            return True
        mock_exists.side_effect = new_exists

        upload_dir = os.path.join('the', 'upload', 'dir')
        work_dir = os.path.join('the', 'work', 'dir')

        # Call method to test
        broker = NfsBroker()
        broker.cleanup_upload_dir(upload_dir, work_dir)

        # Check results
        mock_umount.assert_called_once_with(work_dir)


class TestNfsBrokerDeleteFiles(TestCase):

    def setUp(self):
        django.setup()

    @patch('storage.brokers.nfs_broker.os.path.exists')
    @patch('storage.brokers.nfs_broker.nfs_mount')
    @patch('storage.brokers.nfs_broker.nfs_umount')
    @patch('storage.brokers.nfs_broker.os.remove')
    def test_successfully(self, mock_remove, mock_umount, mock_mount, mock_exists):
        '''Tests calling NfsBroker.delete_files() successfully'''

        def new_exists(path):
            return True
        mock_exists.side_effect = new_exists

        mount = 'host:/dir'
        work_dir = os.path.join('the', 'work', 'dir')
        file_1 = os.path.join('my_dir', 'my_file.txt')
        file_2 = os.path.join('my_dir', 'my_file.json')
        full_path_file_1 = os.path.join(work_dir, file_1)
        full_path_file_2 = os.path.join(work_dir, file_2)

        # Call method to test
        broker = NfsBroker()
        broker.load_config({'type': NfsBroker.broker_type, 'mount': mount})
        broker.delete_files(work_dir, [file_1, file_2])

        # Check results
        mock_mount.assert_called_once_with(mount, work_dir, False)
        two_calls = [call(full_path_file_1), call(full_path_file_2)]
        mock_remove.assert_has_calls(two_calls)
        mock_umount.assert_called_once_with(work_dir)

    @patch('storage.brokers.nfs_broker.os.path.exists')
    @patch('storage.brokers.nfs_broker.nfs_mount')
    @patch('storage.brokers.nfs_broker.nfs_umount')
    @patch('storage.brokers.nfs_broker.os.remove')
    def test_error(self, mock_remove, mock_umount, mock_mount, mock_exists):
        '''Tests calling NfsBroker.delete_files() where there is an error deleting a file'''

        mock_remove.side_effect = Exception
        def new_exists(path):
            return True
        mock_exists.side_effect = new_exists

        mount = 'host:/dir'
        work_dir = os.path.join('the', 'work', 'dir')
        file_1 = os.path.join('my_dir', 'my_file.txt')
        file_2 = os.path.join('my_dir', 'my_file.json')
        full_path_file_1 = os.path.join(work_dir, file_1)
        full_path_file_2 = os.path.join(work_dir, file_2)

        # Call method to test
        broker = NfsBroker()
        broker.load_config({'type': NfsBroker.broker_type, 'mount': mount})
        self.assertRaises(Exception, broker.delete_files, work_dir, [file_1, file_2])

        # Check results
        mock_mount.assert_called_once_with(mount, work_dir, False)
        mock_umount.assert_called_once_with(work_dir)  # Make sure umount was successfully called for cleanup


class TestNfsBrokerDownloadFiles(TestCase):

    def setUp(self):
        django.setup()

    @patch('storage.brokers.nfs_broker.os.makedirs')
    @patch('storage.brokers.nfs_broker.os.path.exists')
    @patch('storage.brokers.nfs_broker.execute_command_line')
    def test_successfully(self, mock_execute, mock_exists, mock_makedirs):
        '''Tests calling NfsBroker.download_files() successfully'''

        def new_exists(path):
            return False
        mock_exists.side_effect = new_exists

        download_dir = os.path.join('the', 'download', 'dir')
        work_dir = os.path.join('the', 'work', 'dir')
        file_1 = 'my_file.txt'
        file_2 = 'my_file.json'
        local_path_file_1 = os.path.join('my_dir_1', file_1)
        local_path_file_2 = os.path.join('my_dir_2', file_2)
        workspace_path_file_1 = os.path.join('my_wrk_dir_1', file_1)
        workspace_path_file_2 = os.path.join('my_wrk_dir_2', file_2)
        full_local_path_file_1 = os.path.join(download_dir, local_path_file_1)
        full_local_path_file_2 = os.path.join(download_dir, local_path_file_2)
        full_workspace_path_file_1 = os.path.join(work_dir, workspace_path_file_1)
        full_workspace_path_file_2 = os.path.join(work_dir, workspace_path_file_2)
        full_local_path_dir_1 = os.path.dirname(full_local_path_file_1)
        full_local_path_dir_2 = os.path.dirname(full_local_path_file_2)

        # Call method to test
        broker = NfsBroker()
        broker.download_files(download_dir, work_dir, [(workspace_path_file_1, local_path_file_1),
                                                       (workspace_path_file_2, local_path_file_2)])

        # Check results
        two_calls = [call(full_local_path_dir_1, mode=0755),
                     call(full_local_path_dir_2, mode=0755)]
        mock_makedirs.assert_has_calls(two_calls)
        two_calls = [call(['ln', '-s', full_workspace_path_file_1, full_local_path_file_1]),
                     call(['ln', '-s', full_workspace_path_file_2, full_local_path_file_2])]
        mock_execute.assert_has_calls(two_calls)


class TestNfsBrokerIsConfigValid(TestCase):

    def setUp(self):
        django.setup()

    def test_successfully(self):
        '''Tests calling NfsBroker.is_config_valid() successfully'''

        mount = 'host:/dir'

        # Call method to test
        broker = NfsBroker()
        # No exception is success
        broker.is_config_valid({'type': NfsBroker.broker_type, 'mount': mount})

    def test_bad_broker(self):
        '''Tests calling NfsBroker.is_config_valid() with a bad broker value'''

        mount = 'host:/dir'

        # Call method to test
        broker = NfsBroker()
        self.assertRaises(Exception, broker.is_config_valid, {'type': 'BAD', 'mount': mount})

    def test_missing_mount(self):
        '''Tests calling NfsBroker.is_config_valid() with a missing mount value'''

        # Call method to test
        broker = NfsBroker()
        self.assertRaises(Exception, broker.is_config_valid, {'type': NfsBroker.broker_type})

    def test_bad_mount(self):
        '''Tests calling NfsBroker.is_config_valid() with a bad mount value'''

        # Call method to test
        broker = NfsBroker()
        self.assertRaises(Exception, broker.is_config_valid, {'type': NfsBroker.broker_type, 'mount': 123})


class TestNfsBrokerLoadConfig(TestCase):

    def setUp(self):
        django.setup()

    def test_successfully(self):
        '''Tests calling NfsBroker.load_config() successfully'''

        mount = 'host:/dir'

        # Call method to test
        broker = NfsBroker()
        broker.load_config({'type': NfsBroker.broker_type, 'mount': mount})

        self.assertEqual(broker.mount, mount)


class TestNfsBrokerMoveFiles(TestCase):

    def setUp(self):
        django.setup()

    @patch('storage.brokers.nfs_broker.os.makedirs')
    @patch('storage.brokers.nfs_broker.os.path.exists')
    @patch('storage.brokers.nfs_broker.os.chmod')
    @patch('storage.brokers.nfs_broker.nfs_mount')
    @patch('storage.brokers.nfs_broker.nfs_umount')
    @patch('storage.brokers.nfs_broker.shutil.move')
    def test_successfully(self, mock_move, mock_umount, mock_mount, mock_chmod, mock_exists, mock_makedirs):
        '''Tests calling NfsBroker.move_files() successfully'''

        def new_exists(path):
            return False
        mock_exists.side_effect = new_exists

        mount = 'host:/dir'
        work_dir = os.path.join('the', 'work', 'dir')
        file_1 = 'my_file.txt'
        file_2 = 'my_file.json'
        old_workspace_path_1 = os.path.join('my_dir_1', file_1)
        old_workspace_path_2 = os.path.join('my_dir_2', file_1)
        new_workspace_path_1 = os.path.join('my_new_dir_1', file_1)
        new_workspace_path_2 = os.path.join('my_new_dir_2', file_1)
        full_old_workspace_path_1 = os.path.join(work_dir, old_workspace_path_1)
        full_old_workspace_path_2 = os.path.join(work_dir, old_workspace_path_2)
        full_new_workspace_path_1 = os.path.join(work_dir, new_workspace_path_1)
        full_new_workspace_path_2 = os.path.join(work_dir, new_workspace_path_2)

        # Call method to test
        broker = NfsBroker()
        broker.load_config({'type': NfsBroker.broker_type, 'mount': mount})
        broker.move_files(work_dir, [(old_workspace_path_1, new_workspace_path_1), (old_workspace_path_2, new_workspace_path_2)])

        # Check results
        mock_mount.assert_called_once_with(mount, work_dir, False)
        two_calls = [call(os.path.dirname(full_new_workspace_path_1), mode=0755),
                     call(os.path.dirname(full_new_workspace_path_2), mode=0755)]
        mock_makedirs.assert_has_calls(two_calls)
        two_calls = [call(full_old_workspace_path_1, full_new_workspace_path_1), call(full_old_workspace_path_2, full_new_workspace_path_2)]
        mock_move.assert_has_calls(two_calls)
        mock_umount.assert_called_once_with(work_dir)


    @patch('storage.brokers.nfs_broker.os.path.exists')
    @patch('storage.brokers.nfs_broker.nfs_mount')
    @patch('storage.brokers.nfs_broker.nfs_umount')
    @patch('storage.brokers.nfs_broker.shutil.move')
    def test_error(self, mock_move, mock_umount, mock_mount, mock_exists):
        '''Tests calling NfsBroker.move_files() where there is an error moving a file'''

        mock_move.side_effect = Exception
        def new_exists(path):
            return True
        mock_exists.side_effect = new_exists

        mount = 'host:/dir'
        work_dir = os.path.join('the', 'work', 'dir')
        file_1 = 'my_file.txt'
        file_2 = 'my_file.json'
        old_workspace_path_1 = os.path.join('my_dir_1', file_1)
        old_workspace_path_2 = os.path.join('my_dir_2', file_1)
        new_workspace_path_1 = os.path.join('my_new_dir_1', file_1)
        new_workspace_path_2 = os.path.join('my_new_dir_2', file_1)
        full_old_workspace_path_1 = os.path.join(work_dir, old_workspace_path_1)
        full_old_workspace_path_2 = os.path.join(work_dir, old_workspace_path_2)
        full_new_workspace_path_1 = os.path.join(work_dir, new_workspace_path_1)
        full_new_workspace_path_2 = os.path.join(work_dir, new_workspace_path_2)

        # Call method to test
        broker = NfsBroker()
        broker.load_config({'type': NfsBroker.broker_type, 'mount': mount})
        self.assertRaises(Exception, broker.move_files, work_dir, [(old_workspace_path_1, new_workspace_path_1),
                                                                   (old_workspace_path_2, new_workspace_path_2)])

        # Check results
        mock_mount.assert_called_once_with(mount, work_dir, False)
        mock_umount.assert_called_once_with(work_dir)  # Make sure umount was successfully called for d


class TestNfsBrokerSetupDownloadDir(TestCase):

    def setUp(self):
        django.setup()

    @patch('storage.brokers.nfs_broker.nfs_mount')
    def test_successfully(self, mock_mount):
        '''Tests calling NfsBroker.setup_download_dir() successfully'''

        mount = 'host:/dir'
        download_dir = os.path.join('the', 'download', 'dir')
        work_dir = os.path.join('the', 'work', 'dir')

        # Call method to test
        broker = NfsBroker()
        broker.load_config({'type': NfsBroker.broker_type, 'mount': mount})
        broker.setup_download_dir(download_dir, work_dir)

        # Check results
        mock_mount.assert_called_once_with(mount, work_dir, True)


class TestNfsBrokerSetupUploadDir(TestCase):

    def setUp(self):
        django.setup()

    def test_successfully(self):
        '''Tests calling NfsBroker.setup_upload_dir() successfully'''

        mount = 'host:/dir'
        upload_dir = os.path.join('the', 'upload', 'dir')
        work_dir = os.path.join('the', 'work', 'dir')

        # Call method to test
        broker = NfsBroker()
        broker.load_config({'type': NfsBroker.broker_type, 'mount': mount})
        broker.setup_upload_dir(upload_dir, work_dir)


class TestNfsBrokerUploadFiles(TestCase):

    def setUp(self):
        django.setup()

    @patch('storage.brokers.nfs_broker.os.makedirs')
    @patch('storage.brokers.nfs_broker.os.path.exists')
    @patch('storage.brokers.nfs_broker.os.chmod')
    @patch('storage.brokers.nfs_broker.nfs_mount')
    @patch('storage.brokers.nfs_broker.nfs_umount')
    @patch('storage.brokers.nfs_broker.shutil.copy')
    def test_successfully(self, mock_copy, mock_umount, mock_mount, mock_chmod, mock_exists, mock_makedirs):
        '''Tests calling NfsBroker.upload_files() successfully'''

        def new_exists(path):
            return False
        mock_exists.side_effect = new_exists

        mount = 'host:/dir'
        upload_dir = os.path.join('the', 'upload', 'dir')
        work_dir = os.path.join('the', 'work', 'dir')
        work_dir2 = os.path.join(os.sep, 'the', 'work', 'dir')
        file_1 = 'my_file.txt'
        file_2 = 'my_file.json'
        local_path_file_1 = os.path.join('my_dir_1', file_1)
        local_path_file_2 = os.path.join('my_dir_2', file_2)
        workspace_path_file_1 = os.path.join('my_wrk_dir_1', file_1)
        workspace_path_file_2 = os.path.join('my_wrk_dir_2', file_2)
        workspace_path_file_3 = os.path.join(os.sep, 'my_wrk_dir_2', file_2)
        full_local_path_file_1 = os.path.join(upload_dir, local_path_file_1)
        full_local_path_file_2 = os.path.join(upload_dir, local_path_file_2)
        full_workspace_path_file_1 = os.path.join(work_dir, workspace_path_file_1)
        full_workspace_path_file_2 = os.path.join(work_dir, workspace_path_file_2)
        full_workspace_path_file_3 = os.path.join(work_dir2, workspace_path_file_2)

        # Call method to test
        mountstats_data = '''16 36 0:3 / /proc rw,nosuid,nodev,noexec,relatime shared:5 - proc proc rw
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
''' % (os.path.abspath(work_dir),)
        mo = mock_open(read_data=mountstats_data)
        # need to patch readlines() since only read() is patched in mock_open
        mo.return_value.readlines.return_value = mo.return_value.read.return_value.split('\n')
        with patch('__builtin__.open', mo, create=True) as pmo:
            broker = NfsBroker()
            broker.load_config({'type': NfsBroker.broker_type, 'mount': mount})
            broker.upload_files(upload_dir, work_dir, [(local_path_file_1, workspace_path_file_1),
                                                       (local_path_file_2, workspace_path_file_2),
                                                       (local_path_file_2, workspace_path_file_3)])

        # Check results
        mock_mount.assert_called_once_with(mount, work_dir, False)
        two_calls = [call(os.path.dirname(full_workspace_path_file_1), mode=0755),
                     call(os.path.dirname(full_workspace_path_file_2), mode=0755)]
        mock_makedirs.assert_has_calls(two_calls)
        two_calls = [call(full_local_path_file_1, full_workspace_path_file_1), call(full_local_path_file_2, full_workspace_path_file_2)]
        mock_copy.assert_has_calls(two_calls)
        mock_umount.assert_called_once_with(work_dir)

    @patch('storage.brokers.nfs_broker.os.path.exists')
    @patch('storage.brokers.nfs_broker.nfs_mount')
    @patch('storage.brokers.nfs_broker.nfs_umount')
    @patch('storage.brokers.nfs_broker.shutil.copy')
    def test_error(self, mock_copy, mock_umount, mock_mount, mock_exists):
        '''Tests calling NfsBroker.upload_files() where there is an error copying a file'''

        mock_copy.side_effect = Exception
        def new_exists(path):
            return True
        mock_exists.side_effect = new_exists

        mount = 'host:/dir'
        upload_dir = os.path.join('the', 'upload', 'dir')
        work_dir = os.path.join('the', 'work', 'dir')
        file_1 = 'my_file.txt'
        file_2 = 'my_file.json'
        local_path_file_1 = os.path.join('my_dir_1', file_1)
        local_path_file_2 = os.path.join('my_dir_2', file_2)
        workspace_path_file_1 = os.path.join('my_wrk_dir_1', file_1)
        workspace_path_file_2 = os.path.join('my_wrk_dir_2', file_2)
        full_local_path_file_1 = os.path.join(upload_dir, local_path_file_1)
        full_local_path_file_2 = os.path.join(upload_dir, local_path_file_2)
        full_workspace_path_file_1 = os.path.join(work_dir, workspace_path_file_1)
        full_workspace_path_file_2 = os.path.join(work_dir, workspace_path_file_2)

        # Call method to test
        broker = NfsBroker()
        broker.load_config({'type': NfsBroker.broker_type, 'mount': mount})
        self.assertRaises(Exception, broker.upload_files, upload_dir, work_dir, [(local_path_file_1, workspace_path_file_1),
                                                                                 (local_path_file_1, workspace_path_file_1)])

        # Check results
        mock_mount.assert_called_once_with(mount, work_dir, False)
        mock_umount.assert_called_once_with(work_dir)  # Make sure umount was successfully called for cleanup

@skipIf(not sys.platform.startswith("linux"), u'umount test is only available on linux.')
@skipIf("TRAVIS" in os.environ, u'sudo is not available in travis-ci.')
class TestNfsUmount(TestCase):
    def setUp(self):
        django.setup()
        self.mntdir = tempfile.mkdtemp()
    
    def tearDown(self):
        os.rmdir(self.mntdir)

    def test_umount_if_not_mounted(self):
        '''Tests unmounting a location that isn't currently mounted to ensure there isn't an error.'''
        nfs_umount(self.mntdir)  # should not throw an exception because the mount location isn't mounted
