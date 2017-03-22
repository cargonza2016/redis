# Copyright 2015 Canonical Ltd.
# Licensed under the GPLv3, see copyright file for details.

"""Utilities for working with the redis configuration file."""

import errno
import os
import shutil
import tempfile

import settings


def include_config(target):
    """Include target configuration file at the end of the default config.

    Note that this function is not idempotent. For this reason, it is only safe
    to call it in the install hook.

    Raise an IOError if the configuration file does not exist or it is not
    writable.
    """
    _backup(settings.DEFAULT_REDIS_CONF)
    with open(settings.DEFAULT_REDIS_CONF, 'a') as conf_file:
        conf_file.write('include {}\n'.format(target))


def write(options, target):
    """Write the redis customized configuration file.

    Receive the redis charm configuration options and the target file where to
    write configuration to.

    Report whether the new and old configurations differ.
    Raise an IOError if a problem is encountered in the operation.
    """
    try:
        old_content = open(target, 'r').read()
    except IOError as err:
        if err.errno != errno.ENOENT:
            raise
        # It is acceptable that the customized configuration does not exist.
        old_content = ''
    new_content = ''.join(
        '{} {}\n'.format(key, value) for key, value in sorted(options.items()))
    # If there are no differences in the new and old configuration, we can
    # avoid writing the file and/or doing backups.
    if new_content == old_content:
        return False
    # The backup is only done if the target file has content.
    if old_content:
        _backup(target)
    # Write the new configuration in a new file, then rename to the real file.
    # Since the renaming operation may fail on some Unix flavors if the source
    # and destination files are on different file systems, use for the
    # temporary file the same directory where the target is stored.
    dirname = os.path.dirname(target)
    temp_file = tempfile.NamedTemporaryFile(
        prefix='charm-new-config-', dir=dirname, delete=False)
    temp_file.write(new_content)
    # Ensure that all the data is written to disk.
    temp_file.flush()
    os.fsync(temp_file.fileno())
    temp_file.close()
    os.chmod(temp_file.name, 0644)
    # Rename the temporary file to the real target file.
    os.rename(temp_file.name, target)
    return True


def _backup(filename):
    """Create a backup copy of the given file.

    Return the path to the backup copy.
    Raise an IOError if a problem occurs while copying the file.
    """
    backup_filename = filename + '.bak'
    shutil.copyfile(filename, backup_filename)
    return backup_filename
