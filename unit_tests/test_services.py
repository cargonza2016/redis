# Copyright 2015 Canonical Ltd.
# Licensed under the GPLv3, see copyright file for details.

from pkg_resources import resource_filename
import sys
import unittest

import mock

# Allow importing modules and packages from the hooks directory.
sys.path.append(resource_filename(__name__, '../hooks'))

import services


@mock.patch('hookutils.log', mock.Mock())
@mock.patch('charmhelpers.core.hookenv.log', mock.Mock())
@mock.patch('charmhelpers.core.hookenv.relation_ids', mock.MagicMock())
@mock.patch('charmhelpers.core.hookenv.config')
@mock.patch('charmhelpers.core.services.base.ServiceManager')
class TestManage(unittest.TestCase):

    def test_services(self, mock_manager, mock_config):
        services.manage()
        self.assertEqual(1, mock_manager.call_count)
        definitions = mock_manager.call_args[0][0]
        service_names = [i['service'] for i in definitions]
        self.assertEqual(['redis-master', 'redis-slave'], service_names)
        mock_config.assert_called_once_with()
