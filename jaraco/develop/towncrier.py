import collections
import pathlib
import subprocess
import sys

import autocommand
from jaraco.vcs import repo
from jaraco.versioning import semver


_release_bumps = collections.defaultdict(
    feature='minor',
    bugfix='patch',
    doc='minor',
    removal='major',
    misc='patch',
)
"""
Map the towncrier default fragment types to semver bumps.
"""


def _release_bump(file):
    """
    Given a towncrier fragment file, determine the
    semver release bump.
    """
    _, type_, _ = file.name.split('.', 2)
    return _release_bumps[type_]


def release_kind():
    """
    Determine which release to make based on the files in the
    changelog.
    """
    path = pathlib.Path('newsfragments')
    fragments = path.iterdir() if path.exists() else ()
    bumps = map(_release_bump, fragments)
    # use min here as 'major' < 'minor' < 'patch'
    return min(bumps, default='patch')


def get_version():
    """
    >>> str(get_version())
    '...'
    """
    return repo().get_next_version(release_kind())


@autocommand.autocommand(__name__)
def run(command, *args):
    cmd = (
        sys.executable,
        '-m',
        'towncrier',
        command,
        '--version',
        semver(get_version()),
    ) + args
    subprocess.check_call(cmd)
