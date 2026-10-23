import pathlib
import subprocess
import sys

from jaraco.vcs import repo
from jaraco.versioning import semver

_release_bumps = dict(
    feature='minor',
    bugfix='patch',
    doc='patch',
    removal='major',
    misc='patch',
)
"""
Map the towncrier default fragment types to semver bumps.
"""


def _fragment_type(file):
    """
    Given a towncrier fragment file, infer its type, or None if the
    name declares no recognized type.

    Parse from the right, as towncrier does, so a dot in the id
    doesn't shift the fields.

    >>> _fragment_type(pathlib.Path('18.feature.rst'))
    'feature'
    >>> _fragment_type(pathlib.Path('+drop-python-3.10.feature.rst'))
    'feature'
    >>> _fragment_type(pathlib.Path('18.feature'))
    'feature'
    >>> _fragment_type(pathlib.Path('notes.rst'))
    """
    parts = file.name.rsplit('.', 2)
    return next((part for part in parts[-2:] if part in _release_bumps), None)


def _release_bump(file):
    """
    Given a towncrier fragment file, determine the
    semver release bump.
    """
    return _release_bumps[_fragment_type(file)]


def news_fragments():
    except_ = 'README.rst', '.gitignore'
    path = pathlib.Path('newsfragments')
    return (file for file in path.glob('*') if file.name not in except_)


def release_kind():
    """
    Determine which release to make based on the files in the
    changelog.
    """
    check_changes()
    bumps = map(_release_bump, news_fragments())
    # use min here as 'major' < 'minor' < 'patch'
    return min(bumps, default='patch')


def check_changes():
    """
    Verify that all of the news fragments have the appropriate names.
    """
    unrecognized = [
        str(file) for file in news_fragments() if _fragment_type(file) is None
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
