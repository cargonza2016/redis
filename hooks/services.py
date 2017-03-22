#!/usr/bin/python

# Copyright 2015 Canonical Ltd.
# Licensed under the GPLv3, see copyright file for details.

"""Redis charm service definitions and management.

This charm uses the service framework to handle all of its hooks except for the
install hook. See https://pythonhosted.org/charmhelpers/examples/services.html

Two service definitions are provided to the manager: redis-master and
redis-slave. The idea is that either the former or the latter can be ready at
the same time, but not both or none. If the "redis1:master redis2:slave"
relation is established and ready, then the redis-slave service definition is
enabled on redis2 units. In all the other cases the redis-master definition is
enabled.

The redis server itself is always running, and it is only restarted when a
change is detected in its configuration file, due to charm config changes or to
slave relation established.
"""

import functools

from charmhelpers.core import hookenv
from charmhelpers.core.services import base

import hookutils
import serviceutils
import relations


@hookutils.hook_name_logged
def manage():
    """Set up the service manager for redis."""
    config = hookenv.config()
    service_start = functools.partial(
        serviceutils.service_start, config['port'], config.previous('port'))
    service_stop = functools.partial(serviceutils.service_stop, config['port'])
    # Handle relations.
    db_relation = relations.DbRelation()
    master_relation = relations.MasterRelation()
    slave_relation = relations.SlaveRelation()
    slave_relation_ready = slave_relation.is_ready()

    # Set up the service manager.
    manager = base.ServiceManager([
        {
            # The name of the redis master service.
            'service': 'redis-master',

            # Ports to open when the service starts.
            'ports': [config['port']],

            # Context managers for provided relations.
            'provided_data': [db_relation, master_relation],

            # Data (contexts) required to start the service.
            'required_data': [config, not slave_relation_ready],

            # Callables called when required data is ready.
            'data_ready': [
                serviceutils.write_config_file(
                    config,
                    db_relation=db_relation,
                    master_relation=master_relation),
            ],

            # Callables called when it is time to start the service.
            'start': [service_start],

            # Callables called when it is time to stop the service.
            'stop': [service_stop],
        },
        {
            # The name of the redis slave service.
            'service': 'redis-slave',

            # Ports to open when the service starts.
            'ports': [config['port']],

            # Context managers for provided relations.
            'provided_data': [db_relation],

            # Data (contexts) required to start the service.
            'required_data': [config, slave_relation_ready],

            # Callables called when required data is ready.
            'data_ready': [
                serviceutils.write_config_file(
                    config,
                    db_relation=db_relation,
                    slave_relation=slave_relation),
            ],

            # Callables called when it is time to start the service.
            'start': [service_start],

            # Callables called when it is time to stop the service.
            'stop': [service_stop],
        }
    ])
    manager.manage()
