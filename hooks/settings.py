# Copyright 2015 Canonical Ltd.
# Licensed under the GPLv3, see copyright file for details.

"""Charm settings/constants used by the Python hook modules."""


# Define the paths to the redis default and customized configuration files.
DEFAULT_REDIS_CONF = '/etc/redis/redis.conf'
REDIS_CONF = '/etc/redis/redis-charm.conf'

# Define Debian packages to be installed.
PACKAGES = ['redis-server']

# Define the name of the init service set up when installing redis.
SERVICE_NAME = 'redis-server'
