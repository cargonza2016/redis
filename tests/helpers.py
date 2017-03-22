# Copyright 2015 Canonical Ltd.
# Licensed under the GPLv3, see copyright file for details.

"""Redis charm functional tests helpers."""

import itertools
import telnetlib

import amulet
from amulet.helpers import environments


# Define the charm name.
CHARM_NAME = 'redis'
# Define the deployment timeout in seconds.
_TIMEOUT = 30 * 60


class RedisClient(object):
    """A very simple and naive telnet redis client used for tests."""

    def __init__(self, host, port=6379):
        """Initialize the client."""
        self._host = host
        self._port = port
        self._client = None

    def connect(self, password=None):
        """Connect to the client."""
        self._client = telnetlib.Telnet(self._host, self._port)
        if password is not None:
            self._client.write('AUTH {}\n'.format(password))
            response = self._readline()
            if response != '+OK':
                raise ValueError('authentication error: {}'.format(response))

    def close(self):
        """Close the client connection."""
        if self._client is not None:
            self._client.close()
        self._client = None

    def set(self, key, value):
        """Set a key in the redis database, with the given value."""
        self._client.write('SET {} {}\n'.format(key, value))
        response = self._readline()
        if response != '+OK':
            raise ValueError('unexpected response: {}'.format(response))

    def get(self, key):
        """Return the value corresponding to key from the redis database.

        Return None if the key is not found.
        """
        self._client.write('GET {}\n'.format(key))
        response = self._readline()
        if response == '$-1':
            return None
        return self._readline()

    def _readline(self):
        """Read next line from the client connection."""
        return self._client.read_until('\r\n').strip()


def get_environment_type():
    """Return the current environment type."""
    envs = environments()['environments']
    return envs[amulet.default_environment()]['type']


def get_private_address(unit):
    """Return the private address of the given sentry unit."""
    address, retcode = unit.run('unit-get private-address')
    assert retcode == 0, 'error retrieving unit private address'
    return address


def deploy(options=None):
    """Deploy one unit of the given service using the redis charm.

    Return the Amulet deployment and the unit object.
    """
    deployment = amulet.Deployment(series='trusty')
    service_name = _get_service_name()
    deployment.add(service_name, charm=CHARM_NAME)
    if options is not None:
        deployment.configure(service_name, options)
    deployment.expose(service_name)
    try:
        deployment.setup(timeout=_TIMEOUT)
        deployment.sentry.wait()
    except amulet.helpers.TimeoutError:
        amulet.raise_status(
            amulet.FAIL, msg='Environment was not stood up in time.')
    return deployment, deployment.sentry.unit[service_name + '/0']


def deploy_master_slave(master_options=None, slave_options=None):
    """Deploy two redis services related in a master-slave relationship.

    Return the Amulet deployment and the two unit objects.
    """
    deployment = amulet.Deployment(series='trusty')
    master, slave = _get_service_name(), _get_service_name()
    deployment.add(master, charm=CHARM_NAME)
    deployment.add(slave, charm=CHARM_NAME)
    if master_options is not None:
        deployment.configure(master, master_options)
    if slave_options is not None:
        deployment.configure(slave, slave_options)
    deployment.relate(master + ':master', slave + ':slave')
    deployment.expose(master)
    deployment.expose(slave)
    try:
        deployment.setup(timeout=_TIMEOUT)
        deployment.sentry.wait()
    except amulet.helpers.TimeoutError:
        amulet.raise_status(
            amulet.FAIL, msg='Environment was not stood up in time.')
    units = deployment.sentry.unit
    return deployment, units[master + '/0'], units[slave + '/0']


_counter = itertools.count()


def _get_service_name():
    """Return an incremental redis service name."""
    return 'redis{}'.format(next(_counter))
