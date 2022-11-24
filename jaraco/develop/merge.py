import re
import textwrap
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

    def __init__(self, match):
        self.match = match

    def __getattr__(self, name):
        return self.match.groupdict()[name]

    @classmethod
    def find(cls, text):
        matches = re.finditer(
            r'^(?P<left_desc><<<<<<<.*?\n)'
            r'(?P<left>(.|\n)*?)'
            r'^(=======\n)'
            r'(?P<right>(.|\n)*?)'
            r'^(?P<right_desc>>>>>>>>.*?\n)',
            text,
            re.MULTILINE,
        )
        return map(cls, matches)

    def replace(self, repl, orig):
        return orig.replace(self.match.group(0), repl)


def resolve(conflict):
    if 'skeleton' not in conflict.right:
        raise ValueError("Unable to resolve")
    name = re.search('name = (.*)', Path('setup.cfg').read_text()).group(1)
    return conflict.right.replace('skeleton', name)


@autocommand.autocommand(__name__)
def merge(base: Path, local: Path, remote: Path, merge: Path):
    orig = merge.read_text()
    conflicts = Conflict.find(orig)
    for conflict in conflicts:
        orig = conflict.replace(resolve(conflict), orig)
    merge.write_text(orig)
