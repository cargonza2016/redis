# Copyright 2015 Canonical Ltd.
# Licensed under the GPLv3, see copyright file for details.

"""Service manager helpers.

This module includes closures and callbacks suitable to be used when
registering callables in the services framework manager.
"""

from charmhelpers import fetch
from charmhelpers.core import (
    hookenv,
    host,
)

import configfile
import hookutils
import settings


def service_start(port, previous_port, service_name):
    """Start the service if not already running.

    Receive the current port on which the redis server is listening to and the
    previous one. Open/close the Juju ports accordingly.
    """
    if not host.service_running(settings.SERVICE_NAME):
        hookutils.log('Starting service {}.'.format(service_name))
        host.service_start(settings.SERVICE_NAME)
    if previous_port is not None:
        hookenv.close_port(previous_port)
    hookenv.open_port(port)


def service_stop(port, service_name):
    """Stop the service if it is running and if the stop hook is executing.

    Receive the current port on which the redis server is listening to.

    If the stop hook is executing, also close the service ports and remove the
    redis package and its configuration files.
    """
    if hookenv.hook_name() != 'stop':
        # There is no need to stop the service if we are not in the stop hook.
        return
    if host.service_running(settings.SERVICE_NAME):
        hookutils.log('Stopping service {}.'.format(service_name))
        host.service_stop(settings.SERVICE_NAME)
    # Close the service port.
    hookenv.close_port(port)
    # Remove redis package and clean up files.
    hookutils.log('Removing system packages.')
    fetch.apt_purge(settings.PACKAGES)


def write_config_file(
        config, db_relation=None, master_relation=None, slave_relation=None):
    """Wrap the configfile.write function building options for the config.

    The config argument is the hook environment configuration.
    The relation arguments are relation context, and when passed they are
    assumed to be ready.

    Return a function that can be used as a callback in the services framework,
    and that generates the redis configuration file.

    This returned functions also takes care of restarting the service if the
    configuration changed.
    """
    def callback(service_name):
        options = _get_service_options(config, slave_relation)
        hookutils.log(
            'Writing configuration file for {}.'.format(service_name))
        changed = configfile.write(options, settings.REDIS_CONF)
        if changed:
            hookutils.log('Restarting service due to configuration change.')
            host.service_restart(settings.SERVICE_NAME)
            # If the configuration changed, it is possible that related units
            # require notification of changes. For this reason, update all the
            # existing established relations. This is required because
            # "services.provide_data" is only called when the current hook
            # is a relation joined or changed.
            _update_relations(filter(None, [db_relation, master_relation]))
        else:
            hookutils.log('No changes detected in the configuration file.')

    return callback


def _get_service_options(config, slave_relation=None):
    """Return a dict containing the redis service configuration options.

    Receive the hook environment config object and optionally the slave
    relation context.
    """
    hookutils.log('Retrieving service options.')
    # To introduce more redis configuration options in the charm, add them to
    # the config.yaml file and to the dictionary returned by this function.
    # If the new options are relevant while establishing relations, also update
    # the "provide_data" methods in the relation contexts defined in
    # relations.py.
    options = {
        'bind': hookenv.unit_private_ip(),
        'databases': config['databases'],
        'logfile': config['logfile'],
        'loglevel': config['loglevel'],
        'port': config['port'],
        'tcp-keepalive': config['tcp-keepalive'],
        'timeout': config['timeout'],
    }
    password = config['password'].strip()
    if password:
        options['requirepass'] = password
    if slave_relation is not None:
        hookutils.log('Setting up slave relation.')
        # If slave_relation is defined, it is assumed that the relation is
        # ready, i.e. that the slave_relation dict evaluates to True.
        data = slave_relation[slave_relation.name][0]
        options['slaveof'] = '{hostname} {port}'.format(**data)
        password = data.get('password')
        if password:
            options['masterauth'] = password
    return options


def _update_relations(relations):
    """Update existing established relations."""
    for relation in relations:
        name = relation.name
        for relation_id in hookenv.relation_ids(name):
            hookutils.log('Updating data for relation {}.'.format(name))
            hookenv.relation_set(relation_id, relation.provide_data())
