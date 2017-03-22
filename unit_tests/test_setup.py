# Copyright 2015 Canonical Ltd.
# Licensed under the GPLv3, see copyright file for details.

from pkg_resources import resource_filename
import sys
import unittest

import mock

# Allow importing modules and packages from the hooks directory.
sys.path.append(resource_filename(__name__, '../hooks'))

# Import as setupmodule to not interfer with the test runner.
import setup as setupmodule


@mock.patch('os.getcwd', lambda: '/working/dir')
class TestPreInstall(unittest.TestCase):

    def test_commands(self):
        with mock.patch('subprocess.check_call') as mock_check_call:
            setupmodule.pre_install()
        self.assertEqual(3, mock_check_call.call_count)
        mock_check_call.assert_has_calls([
            mock.call(['apt-get', 'update']),
            mock.call(['apt-get', 'install', '-y', 'python-pip']),
            mock.call([
                'pip', 'install', '--no-index', '--no-dependencies',
                '--find-links', 'file:////working/dir/deps',
                '-r', '/working/dir/requirements.pip',
            ])
        ])
