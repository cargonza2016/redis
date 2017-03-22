# Copyright 2015 Canonical Ltd.
# Licensed under the GPLv3, see copyright file for details.

"""Helper functions for handling hooks execution."""

import functools

from charmhelpers.core import hookenv


# Define a Juju log function with a predefined level which is actually printed.
log = functools.partial(hookenv.log, level=hookenv.INFO)


def hook_name_logged(function):
    """Decorate the given function so that the current hook name is logged.

    The given function must accept no arguments.
    """
    @functools.wraps(function)
    def decorated():
        hook_name = hookenv.hook_name()
        log('>>> Entering hook: {}.'.format(hook_name))
        try:
            return function()
        finally:
            log('<<< Exiting hook: {}.'.format(hook_name))
    return decorated
