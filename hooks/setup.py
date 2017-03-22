# Copyright 2015 Canonical Ltd.
# Licensed under the GPLv3, see copyright file for details.

"""Do any setup required before the install hook."""

import os
import subprocess


def pre_install():
    """Handle pre-install requirements and initial charm setup."""
    _install_python_requirements()


def _install_python_requirements():
    """Install the Python requirements included in the "deps" directory."""
    current_dir = os.getcwd()
    deps = os.path.join(current_dir, 'deps')
    requirements = os.path.join(current_dir, 'requirements.pip')
    subprocess.check_call(['apt-get', 'update'])
    subprocess.check_call(['apt-get', 'install', '-y', 'python-pip'])
    subprocess.check_call([
        'pip', 'install', '--no-index', '--no-dependencies',
        '--find-links', 'file:///{}'.format(deps), '-r', requirements])
