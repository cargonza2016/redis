# Copyright 2015 Canonical Ltd.
# Licensed under the GPLv3, see copyright file for details.

"""Define service relations for the redis charm."""

from charmhelpers.core import hookenv
from charmhelpers.core.services import helpers


class DbRelation(helpers.RelationContext):
    """Define the redis db relation.

    Subscribers are provided the server "hostname", "port" and "password"
    values in the relation payload. If the redis server does not use
    authentication, the password is an empty string.
    """

    name = 'db'
    interface = 'redis'

    def provide_data(self):
        """Return data to be relation_set for this interface."""
        config = hookenv.config()
        return {
            'hostname': hookenv.unit_private_ip(),
            'port': config['port'],
            'password': config['password'].strip(),
        }


class MasterRelation(DbRelation):
    """Define the redis master relation."""

    name = 'master'


class SlaveRelation(helpers.RelationContext):
    """Define the redis slave relation."""

    name = 'slave'
    interface = 'redis'
    required_keys = ['hostname', 'port']
