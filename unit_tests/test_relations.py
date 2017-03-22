# Copyright 2015 Canonical Ltd.
# Licensed under the GPLv3, see copyright file for details.

from pkg_resources import resource_filename
import sys
import unittest

import mock

# Allow importing modules and packages from the hooks directory.
sys.path.append(resource_filename(__name__, '../hooks'))

import relations


def patch_config(data):
    """Patch the "charmhelpers.core.hookenv.config" function.

    The mocked function returns the given value.
    """
    return mock.patch(
        'charmhelpers.core.hookenv.config',
        lambda: data)


def patch_unit_get(value):
    """Patch the "charmhelpers.core.hookenv.unit_get" function.

    The mocked function returns the given value.
    """
    return mock.patch(
        'charmhelpers.core.hookenv.unit_get',
        mock.Mock(return_value=value))


@mock.patch('hookutils.log', mock.Mock())
class TestDbRelation(unittest.TestCase):

    def setUp(self):
        relation_ids_path = 'charmhelpers.core.hookenv.relation_ids'
        with mock.patch(relation_ids_path, mock.MagicMock()):
            self.relation = relations.DbRelation()

    def test_provide_data(self):
        with patch_config({'port': 4242, 'password': 'secret!'}):
            with patch_unit_get('1.2.3.4') as mock_unit_get:
                data = self.relation.provide_data()
        expected_data = {
            'hostname': '1.2.3.4',
            'port': 4242,
            'password': 'secret!',
        }
        self.assertEqual(expected_data, data)
        mock_unit_get.assert_called_once_with('private-address')
