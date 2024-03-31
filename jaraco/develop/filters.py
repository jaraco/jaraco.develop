"""
Create keyword and tag selectors for projects.

>>> from . import git
>>> import itertools
>>> projects = git.projects()

>>> keywords = map(Keyword, 'keyring,develop,not keyrings'.split(','))
>>> sel = Selectors(keywords)
>>> sorted(filter(sel, projects))
['jaraco.develop', 'keyring']
>>> keywords = map(Keyword, 'py'.split(','))
>>> tags = map(Tag, 'fork,not lifted'.split(','))
>>> sel = Selectors(itertools.chain(keywords, tags))
>>> list(filter(sel, projects))
['/python/cpython']
"""

import operator

import more_itertools

from .compat.py38 import removeprefix


class Selectable:
    @property
    def indicator(self):
        return removeprefix(self, 'not ')

    @property
    def mode(self):
        return 'excluding' if self.startswith('not ') else 'selecting'

    def invert(self, value: bool):
        return value if self.mode == 'selecting' else not value


class Selectors(list):
    def __call__(self, other):
        buckets = more_itertools.bucket(self, operator.attrgetter('mode'))
        selecting = list(buckets['selecting'])
        excluding = list(buckets['excluding'])
        return (
            not selecting or any(selector(other) for selector in selecting)
        ) and all(selector(other) for selector in excluding)


class Keyword(str, Selectable):
    def __call__(self, other):
        return self.invert(other.__contains__(self.indicator))


class Tag(str, Selectable):
    def __call__(self, other):
        return self.invert(self.indicator in other.tags)
