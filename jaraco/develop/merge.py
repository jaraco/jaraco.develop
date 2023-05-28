import re
import textwrap
import contextlib
from pathlib import Path

import autocommand


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
    def read(cls, path):
        return cls.find(path.read_text(), path=path)

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


def resolve_project(conflict):
    """
    If the text "PROJECT" appears in the conflict on the right,
    assume the whole conflict is about downstream customization
    and prefer the downstream (left).

    See jaraco/skeleton#70 for more context.
    """
    assert 'PROJECT' in conflict.right
    return conflict.left


def resolve_shebang(conflict):
    assert conflict.left.startswith('#!')
    assert conflict.left.count('\n') < 5
    return conflict.right


def resolve(conflict):
    for resolver in (resolve_project, resolve_shebang):
        with contextlib.suppress(Exception):
            return resolver(conflict)
    raise ValueError("Unable to resolve")


@autocommand.autocommand(__name__)
def merge(base: Path, local: Path, remote: Path, merge: Path):
    conflicts = Conflict.read(merge)
    res = merge.read_text()
    for conflict in conflicts:
        res = conflict.replace(resolve(conflict), res)
    merge.write_text(res)
