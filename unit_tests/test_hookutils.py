# Copyright 2015 Canonical Ltd.
# Licensed under the GPLv3, see copyright file for details.

from pkg_resources import resource_filename
import sys
import unittest

import mock

# Allow importing modules and packages from the hooks directory.
sys.path.append(resource_filename(__name__, '../hooks'))

import hookutils


def _successful_hook():
    """An example successful hook used for tests."""
    hookutils.log('executing')
    return 42


def _failing_hook():
    """An example failing hook used for tests."""
    hookutils.log('failing')
    raise TypeError


@mock.patch('charmhelpers.core.hookenv.hook_name')
@mock.patch('hookutils.log')
class TestHookNameLogged(unittest.TestCase):

    def test_successful_hook(self, mock_log, mock_hook_name):
        mock_hook_name.return_value = 'config-changed'
        decorated = hookutils.hook_name_logged(_successful_hook)
        result = decorated()
        self.assertEqual(42, result)
        mock_hook_name.assert_called_once_with()
        self.assertEqual(3, mock_log.call_count)
        mock_log.assert_has_calls([
            mock.call('>>> Entering hook: config-changed.'),
            mock.call('executing'),
            mock.call('<<< Exiting hook: config-changed.'),
        ])

    def test_failing_hook(self, mock_log, mock_hook_name):
        mock_hook_name.return_value = 'start'
        decorated = hookutils.hook_name_logged(_failing_hook)
        with self.assertRaises(TypeError):
            decorated()
        mock_hook_name.assert_called_once_with()
        # Even if the hook raised an exception, exiting it is still logged.
        self.assertEqual(3, mock_log.call_count)
        mock_log.assert_has_calls([
            mock.call('>>> Entering hook: start.'),
            mock.call('failing'),
            mock.call('<<< Exiting hook: start.')
        ])
