# Copyright 2015 Canonical Ltd.
# Licensed under the GPLv3, see copyright file for details.

import os
from pkg_resources import resource_filename
import shutil
import sys
import tempfile
import unittest

import mock

# Allow importing modules and packages from the hooks directory.
sys.path.append(resource_filename(__name__, '../hooks'))

import configfile


class TestIncludeConfig(unittest.TestCase):

    def test_success(self):
        conf = tempfile.NamedTemporaryFile(delete=False)
        self.addCleanup(os.remove, conf.name)
        # Also remove the backup file created in the process.
        self.addCleanup(os.remove, conf.name + '.bak')
        conf.write('content\n')
        conf.close()
        with mock.patch('settings.DEFAULT_REDIS_CONF', conf.name):
            configfile.include_config('/my/customized/config')
        expected_content = 'content\ninclude /my/customized/config\n'
        self.assertEqual(expected_content, open(conf.name, 'r').read())

    def test_not_found(self):
        with mock.patch('settings.DEFAULT_REDIS_CONF', '/no/such/file'):
            with self.assertRaises(IOError) as ctx:
                configfile.include_config('/my/customized/config')
        expected_error = "[Errno 2] No such file or directory: '/no/such/file'"
        self.assertEqual(expected_error, bytes(ctx.exception))


class TestWrite(unittest.TestCase):

    def make_target(self, content=None):
        """Return a target file path in a temporary directory.

        If content is not None, also create the target file itself with the
        given content.
        """
        playground = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, playground)
        target = os.path.join(playground, 'target')
        if content is not None:
            with open(target, 'w') as target_file:
                target_file.write(content)
        return target

    def assert_file_content(self, target, content):
        """Ensure a file exists with the given content."""
        self.assertTrue(os.path.isfile(target))
        self.assertEqual(content, open(target, 'r').read())

    def test_unexisting_target(self):
        target = self.make_target()
        changed = configfile.write({'bind': '1.2.3.4', 'port': 4242}, target)
        self.assertTrue(changed)
        self.assert_file_content(target, 'bind 1.2.3.4\nport 4242\n')
        self.assertFalse(os.path.exists(target + '.bak'))

    def test_existing_target(self):
        target = self.make_target('original content')
        changed = configfile.write({'bind': '1.2.3.4', 'port': 7000}, target)
        self.assertTrue(changed)
        self.assert_file_content(target, 'bind 1.2.3.4\nport 7000\n')
        self.assert_file_content(target + '.bak', 'original content')

    def test_no_changes(self):
        target = self.make_target('bind 1.2.3.4\n')
        changed = configfile.write({'bind': '1.2.3.4'}, target)
        self.assertFalse(changed)
        self.assert_file_content(target, 'bind 1.2.3.4\n')
        self.assertFalse(os.path.exists(target + '.bak'))

    def test_error(self):
        target = self.make_target('original content')
        os.chmod(target, 0)
        self.addCleanup(os.chmod, target, 0666)
        with self.assertRaises(IOError) as ctx:
            configfile.write({'bind': '1.2.3.4'}, target)
        expected_error = "[Errno 13] Permission denied: '{}'".format(target)
        self.assertEqual(expected_error, bytes(ctx.exception))
