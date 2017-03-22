#!/usr/bin/env python3

# Copyright 2015 Canonical Ltd.
# Licensed under the GPLv3, see copyright file for details.

"""Redis charm functional tests.

These tests use the Amulet test helpers:
see https://jujucharms.com/docs/stable/tools-amulet

Connection tests are only run on local environments where the internal unit
addresses are reachable.
"""

from pkg_resources import resource_filename
import sys
import time
import unittest

import helpers

# Allow importing modules and packages from the hooks directory.
sys.path.append(resource_filename(__name__, '../hooks'))

import settings


# Define a test decorator for running the test only if the current environment
# type is local.
only_on_local_environments = unittest.skipIf(
    helpers.get_environment_type() != 'local',
    'only available whe using a local environment')


class TestDeployment(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up the environment and deploy the charm.
        cls.deployment, cls.unit = helpers.deploy()

    @classmethod
    def tearDownClass(cls):
        # Remove the redis service.
        cls.deployment.remove_service(cls.unit.info['service'])

    def test_config_file(self):
        address = helpers.get_private_address(self.unit)
        expected_content = (
            'bind {}\n'
            'databases 16\n'
            'logfile /var/log/redis/redis-server.log\n'
            'loglevel notice\n'
            'port 6379\n'
            'tcp-keepalive 0\n'
            'timeout 0\n'
        ).format(address)
        self.assertEqual(
            expected_content,
            self.unit.file_contents(settings.REDIS_CONF))

    @only_on_local_environments
    def test_connection(self):
        client = helpers.RedisClient(self.unit.info['public-address'])
        client.connect()
        self.addCleanup(client.close)
        self.assertIsNone(client.get('my-key'))
        client.set('my-key', 'my-value')
        self.assertEqual('my-value', client.get('my-key'))


class TestDeploymentOptions(unittest.TestCase):

    options = {
        'databases': 3,
        'port': 4242,
        'password': 'secret',
        'loglevel': 'verbose',
        'logfile': '/tmp/redis.log',
        'timeout': 60,
    }

    @classmethod
    def setUpClass(cls):
        # Set up the environment and deploy the charm.
        cls.deployment, cls.unit = helpers.deploy(options=cls.options)

    @classmethod
    def tearDownClass(cls):
        # Remove the redis service.
        cls.deployment.remove_service(cls.unit.info['service'])

    def test_config_file(self):
        address = helpers.get_private_address(self.unit)
        expected_content = (
            'bind {}\n'
            'databases 3\n'
            'logfile /tmp/redis.log\n'
            'loglevel verbose\n'
            'port 4242\n'
            'requirepass secret\n'
            'tcp-keepalive 0\n'
            'timeout 60\n'
        ).format(address)
        self.assertEqual(
            expected_content,
            self.unit.file_contents(settings.REDIS_CONF))

    @only_on_local_environments
    def test_connection(self):
        client = helpers.RedisClient(
            self.unit.info['public-address'], port=self.options['port'])
        client.connect(password=self.options['password'])
        self.addCleanup(client.close)
        self.assertIsNone(client.get('my-key'))
        client.set('my-key', 'my-value')
        self.assertEqual('my-value', client.get('my-key'))


class TestMasterSlaveRelation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up the environment and deploy the charm.
        cls.deployment, cls.master, cls.slave = helpers.deploy_master_slave()
        cls.master_address = helpers.get_private_address(cls.master)
        cls.slave_address = helpers.get_private_address(cls.slave)

    @classmethod
    def tearDownClass(cls):
        # Remove the redis master and slave services.
        cls.deployment.remove_service(cls.slave.info['service'])
        cls.deployment.remove_service(cls.master.info['service'])

    def test_master_config_file(self):
        expected_content = (
            'bind {}\n'
            'databases 16\n'
            'logfile /var/log/redis/redis-server.log\n'
            'loglevel notice\n'
            'port 6379\n'
            'tcp-keepalive 0\n'
            'timeout 0\n'
        ).format(self.master_address)
        self.assertEqual(
            expected_content,
            self.master.file_contents(settings.REDIS_CONF))

    def test_slave_config_file(self):
        expected_content = (
            'bind {}\n'
            'databases 16\n'
            'logfile /var/log/redis/redis-server.log\n'
            'loglevel notice\n'
            'port 6379\n'
            'slaveof {} 6379\n'
            'tcp-keepalive 0\n'
            'timeout 0\n'
        ).format(self.slave_address, self.master_address)
        self.assertEqual(
            expected_content,
            self.slave.file_contents(settings.REDIS_CONF))

    @only_on_local_environments
    def test_connection(self):
        master_client = helpers.RedisClient(self.master.info['public-address'])
        master_client.connect()
        self.addCleanup(master_client.close)
        master_client.set('my-key', '42')
        # Wait for master and slave synchronization.
        time.sleep(1)
        # Retrieve the value from the slave.
        slave_client = helpers.RedisClient(self.slave.info['public-address'])
        slave_client.connect()
        self.addCleanup(slave_client.close)
        self.assertEqual('42', slave_client.get('my-key'))


class TestMasterSlaveRelationOptions(unittest.TestCase):

    master_options = {'databases': 5, 'password': 'secret'}
    slave_options = {'port': 4747, 'loglevel': 'warning', 'timeout': 42}

    @classmethod
    def setUpClass(cls):
        # Set up the environment and deploy the charm.
        cls.deployment, cls.master, cls.slave = helpers.deploy_master_slave(
            master_options=cls.master_options,
            slave_options=cls.slave_options)
        cls.master_address = helpers.get_private_address(cls.master)
        cls.slave_address = helpers.get_private_address(cls.slave)

    @classmethod
    def tearDownClass(cls):
        # Remove the redis master and slave services.
        cls.deployment.remove_service(cls.slave.info['service'])
        cls.deployment.remove_service(cls.master.info['service'])

    def test_master_config_file(self):
        expected_content = (
            'bind {}\n'
            'databases 5\n'
            'logfile /var/log/redis/redis-server.log\n'
            'loglevel notice\n'
            'port 6379\n'
            'requirepass secret\n'
            'tcp-keepalive 0\n'
            'timeout 0\n'
        ).format(self.master_address)
        self.assertEqual(
            expected_content,
            self.master.file_contents(settings.REDIS_CONF))

    def test_slave_config_file(self):
        expected_content = (
            'bind {}\n'
            'databases 16\n'
            'logfile /var/log/redis/redis-server.log\n'
            'loglevel warning\n'
            'masterauth secret\n'
            'port 4747\n'
            'slaveof {} 6379\n'
            'tcp-keepalive 0\n'
            'timeout 42\n'
        ).format(self.slave_address, self.master_address)
        self.assertEqual(
            expected_content,
            self.slave.file_contents(settings.REDIS_CONF))

    @only_on_local_environments
    def test_connection(self):
        master_client = helpers.RedisClient(self.master.info['public-address'])
        master_client.connect(password=self.master_options['password'])
        self.addCleanup(master_client.close)
        master_client.set('my-key', '42')
        # Wait for master and slave synchronization.
        time.sleep(1)
        # Retrieve the value from the slave.
        slave_client = helpers.RedisClient(
            self.slave.info['public-address'], port=self.slave_options['port'])
        slave_client.connect()
        self.addCleanup(slave_client.close)
        self.assertEqual('42', slave_client.get('my-key'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
