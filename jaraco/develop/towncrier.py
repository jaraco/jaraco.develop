import collections
import pathlib
import subprocess
import sys

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


def news_fragments():
    except_ = 'README.rst', '.gitignore'
    path = pathlib.Path('newsfragments')
    names = (file for file in path.iterdir() if file.name not in except_)
    return names if path.exists() else ()


def release_kind():
    """
    Determine which release to make based on the files in the
    changelog.
    """
    bumps = map(_release_bump, news_fragments())
    # use min here as 'major' < 'minor' < 'patch'
    return min(bumps, default='patch')


def check_changes():
    """
    Verify that all of the news fragments have the appropriate names.
    """
    unrecognized = [
        str(file)
        for file in news_fragments()
        if not any(f".{key}" in file.suffixes for key in _release_bumps)
    ]
    if unrecognized:
        raise ValueError(f"Some news fragments have invalid names: {unrecognized}")


def get_version():
    """
    >>> str(get_version())
    '...'
    """
    return repo().get_next_version(release_kind())


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


if __name__ == '__main__':
    run(*sys.argv[1:])
