"""
Facilities for parsing and resolving common merge conflicts.
"""

import contextlib
import os
import re
import shutil
import tempfile
import textwrap
import unittest.mock
from pathlib import Path

import autocommand

import jaraco.packaging.metadata
from jaraco.functools import identity


sample_conflict = textwrap.dedent(
    """
    start
    <<<<<<< HEAD
    .. image:: https://img.shields.io/pypi/v/jaraco.collections.svg
       :target: `PyPI link`_

    .. image:: https://img.shields.io/pypi/pyversions/jaraco.collections.svg
       :target: `PyPI link`_

    .. _PyPI link: https://pypi.org/project/jaraco.collections
    =======
    .. image:: https://img.shields.io/pypi/v/skeleton.svg
       :target: https://pypi.org/project/skeleton
    .. image:: https://img.shields.io/pypi/pyversions/skeleton.svg
    >>>>>>> 401287d8d0f9fb0365149983f5ca42618f00a6d8
    end
    """
).lstrip()


class Conflict:
    r"""
    >>> cf, = Conflict.find(sample_conflict)
    >>> cf.left_desc
    '<<<<<<< HEAD\n'
    >>> cf.right_desc
    '>>>>>>> 401287d8d0f9fb0365149983f5ca42618f00a6d8\n'
    >>> len(cf.left.splitlines())
    7
    >>> len(cf.right.splitlines())
    3
    >>> print(cf.replace('new\n', sample_conflict), end='')
    start
    new
    end
    """

    def __init__(self, match, **kw):
        self.match = match
        vars(self).update(kw)

    def __getattr__(self, name):
        return self.match.groupdict()[name]

    @classmethod
    def read(cls, merge, **kw):
        return cls.find(merge.read_text(), merge=merge, **kw)

    @classmethod
    def find(cls, text, **kw):
        matches = re.finditer(
            r'^(?P<left_desc><<<<<<<.*?\n)'
            r'(?P<left>(.|\n)*?)'
            r'^(=======\n)'
            r'(?P<right>(.|\n)*?)'
            r'^(?P<right_desc>>>>>>>>.*?\n)',
            text,
            re.MULTILINE,
        )
        return (cls(match, **kw) for match in matches)

    def replace(self, repl, orig):
        return orig.replace(self.match.group(0), repl)


def resolve_placeholders(conflict):
    """
    If the text "PROJECT" appears in the conflict on the right,
    prefer upstream (right) but re-substitute the placeholders.

    For more context, see:
    - jaraco/skeleton#70
    - jaraco/jaraco.develop#5
    - jaraco/jaraco.develop#19
    """
    assert 'PROJECT' in conflict.right
    from . import repo

    return _retain_rtd(conflict.left)(
        repo.sub_placeholders(conflict.right, metadata=load_metadata(conflict))
    )


def load_metadata(conflict):
    """
    Load metadata for the current project.

    If it has a conflict in the pyproject.toml, use the 'local' copy
    to load the metadata. See #19 for rationale.
    """
    with conflict_safe_project(conflict) as dir:
        return jaraco.packaging.metadata.load(dir)


@contextlib.contextmanager
def conflict_safe_project(conflict):
    if conflict.merge.name != 'pyproject.toml':
        yield '.'
        return

    with tempfile.TemporaryDirectory() as dir, pretend_version():
        path = Path(dir)
        shutil.copy(conflict.local, path / 'pyproject.toml')

        yield dir


@contextlib.contextmanager
def pretend_version():
    subs = dict(SETUPTOOLS_SCM_PRETEND_VERSION="0")
    with unittest.mock.patch.dict(os.environ, subs):
        yield


def _retain_rtd(left):
    """
    Retain the RTD enablement.

    If RTD was enabled (uncommented) in left, return a function that
    will enable it on the right. Otherwise, return a pass-through function.

    >>> _retain_rtd('''.. image:: https://readthedocs.org/...''')
    <function _enable_rtd at ...>
    >>> _retain_rtd('''.. .. image:: https://readthedocs.org/...''')
    <function identity at ...>
    """
    enabled = re.search(r'^\.\. image.*readthedocs', left, flags=re.MULTILINE)
    return _enable_rtd if enabled else identity


def _enable_rtd(text):
    """
    Given text with a commented RTD badge, uncomment it.

    >>> print(_enable_rtd('''.. .. image:: https://readthedocs.org/...
    ... ..    :target: https://PROJECT_RTD.readthedocs.io/...'''))
    .. image:: https://readthedocs.org/...
       :target: https://PROJECT_RTD.readthedocs.io/...
    """
    return re.sub(r'^\.\. ', '', text, flags=re.MULTILINE)


def resolve_shebang(conflict):
    assert conflict.left.startswith('#!')
    assert conflict.left.count('\n') < 5
    return conflict.right


def resolve(conflict):
    for resolver in (resolve_placeholders, resolve_shebang):
        with contextlib.suppress(Exception):
            return resolver(conflict)
    raise ValueError("Unable to resolve")


@autocommand.autocommand(__name__)
def merge(base: Path, local: Path, remote: Path, merge: Path):
    conflicts = Conflict.read(**locals())
    res = merge.read_text()
    for conflict in conflicts:
        res = conflict.replace(resolve(conflict), res)
    merge.write_text(res)
