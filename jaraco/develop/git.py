from __future__ import annotations
import contextlib
import functools
import os
import pathlib
import posixpath
import re
import subprocess
import sys
import types
import urllib.parse

import requests
import path
from more_itertools import flatten


class URLScheme:
    """
    >>> scheme = URLScheme.lookup('gh://foo/bar')
    >>> scheme.resolve('gh://foo/bar')
    'https://github.com/foo/bar'
    >>> scheme.apply('https://github.com/foo/bar')
    'gh://foo/bar'

    >>> null_scheme = URLScheme.lookup('unknown://foo/bar')
    >>> bool(null_scheme)
    False
    >>> null_scheme.resolve('unknown://foo/bar')
    'unknown://foo/bar'
    >>> null_scheme.apply('unknown://foo/bar')
    'unknown://foo/bar'

    >>> scheme = URLScheme.lookup('https://github.com/foo/bar')
    >>> scheme
    URLScheme('gh://', 'https://github.com/')
    """

    def __init__(self, prefix, value):
        vars(self).update(locals())
        del self.self

    def __repr__(self):
        return f'{self.__class__.__name__}({self.prefix!r}, {self.value!r})'

    def matches(self, url):
        return url.startswith(self.prefix) or url.startswith(self.value)

    @classmethod
    def parse(cls, line):
        key, scheme = line.split()
        url = key.removeprefix('url.').removesuffix('.insteadof')
        return cls(scheme, url)

    def resolve(self, url):
        return url.replace(self.prefix, self.value)

    def apply(self, url):
        return url.replace(self.value, self.prefix)

    @classmethod
    @functools.lru_cache()
    def load(cls):
        cmd = ['git', 'config', '--get-regexp', r'url\..*\.insteadof']
        lines = subprocess.check_output(cmd, text=True)
        return set(map(cls.parse, lines.splitlines()))

    @classmethod
    def lookup(cls, url):
        checks = (scheme for scheme in cls.load() if scheme.matches(url))
        return next(checks, NullScheme())


class NullScheme:
    def __bool__(self):
        return False

    def apply(self, url):
        return url

    def resolve(self, url):
        return url


class URL(str):
    @property
    def scheme(self):
        return URLScheme.lookup(self)

    @property
    def resolved(self):
        return URL(self.scheme.resolve(self))

    @property
    def applied(self):
        return URL(self.scheme.apply(self))

    def join(self, path):
        return URL(urllib.parse.urljoin(self.resolved, path)).applied

    @property
    def path(self):
        return urllib.parse.urlparse(self.resolved).path


class Project(str):
    """
    >>> p = Project.parse('foo-project [tag1] [tag2] (zero defect, coherent software)')
    >>> p
    'foo-project'
    >>> p.tags
    ['tag1', 'tag2']
    >>> p.topics
    ['zero defect', 'coherent software']
    """

    pattern = re.compile(r'(?P<name>\S+)\s*(?P<rest>.*)$')
    cache: dict[str, Project] = {}

    def __new__(cls, value, **kwargs):
        # Down-cast to a string early.
        value = sys.intern(str(value))
        try:
            return cls.cache[value]
        except KeyError:
            new = super().__new__(cls, value)
            cls.cache[new] = new
            return new

    def __init__(self, value, **kwargs):
        vars(self).update({'tags': [], 'topics': [], **kwargs})

    @classmethod
    def parse(cls, line):
        match = types.SimpleNamespace(**cls.pattern.match(line).groupdict())
        tags = list(re.findall(r'\[(.*?)\]', rest := match.rest.rstrip()))
        topics_assigned = re.match(r'[^\(\)]*\((.+)\)$', rest)
        topics = topics_assigned and map(str.strip, topics_assigned.group(1).split(','))
        return cls(match.name, tags=tags, topics=list(filter(None, topics or ())))

    @classmethod
    def from_path(self, path):
        """
        >>> Project.from_path('pypa/setuptools')
        '/pypa/setuptools'
        >>> Project.from_path('jaraco/jaraco.functools')
        'jaraco.functools'
        """
        from . import github
        local = f'{github.username()}/'
        if path.startswith(local):
            return self(path.removeprefix(local))
        return self(f'/{path.removeprefix("/")}')

    @property
    def rtd_slug(self):
        """
        >>> Project('jaraco.functools').rtd_slug
        'jaracofunctools'
        >>> Project('/pypa/setuptools_scm').rtd_slug
        'setuptools-scm'
        """
        return posixpath.basename(self).replace('.', '').replace('_', '-')

    @property
    def rtd_url(self):
        """
        >>> Project('jaraco.functools').rtd_url
        'https://jaracofunctools.readthedocs.io/'
        >>> Project('/pypa/setuptools_scm').rtd_url
        'https://setuptools-scm.readthedocs.io/'
        """
        return f'https://{self.rtd_slug}.readthedocs.io/'


def resolve(name):
    """
    >>> projects = list(map(resolve, projects()))
    >>> 'gh://jaraco/keyrings.firefox' in projects
    True
    >>> 'gh://pmxbot/pmxbot.nsfw' in projects
    True
    """
    from . import github
    default = URL(f'https://github.com/{github.username()}/')
    return default.join(name)


def resolve_repo_name(name):
    """
    >>> resolve_repo_name('keyring')
    'jaraco/keyring'
    >>> resolve_repo_name('/pypa/setuptools')
    'pypa/setuptools'
    """
    return resolve(name).path.removeprefix(posixpath.sep)


def target_for_root(project, root: path.Path = path.Path()):
    """
    Append the prefix of the resolved project name to the target
    and ensure it exists.
    """
    _, prefix, *_ = pathlib.PosixPath(resolve(project).path).parts
    return root / prefix


def configure_fork(project, repo):
    if 'fork' not in project.tags:
        return
    cmd = ['gh', 'repo', 'fork', '--remote']
    subprocess.check_call(cmd, cwd=repo)
    cmd = ['git', 'config', '--local', 'branch.main.remote', 'upstream']
    subprocess.check_call(cmd, cwd=repo)
    cmd = ['git', 'remote', 'get-url', 'origin']
    origin = subprocess.check_output(cmd, cwd=repo).strip()
    cmd = ['git', 'remote', 'set-url', '--push', 'upstream', origin]
    subprocess.check_output(cmd, cwd=repo)


def make_args(**kwargs):
    """
    Create a list of args to git out of kwargs.

    >>> make_args(depth=50, quiet=True)
    ['--depth', '50', '--quiet']
    """
    return list(
        flatten(
            (f'--{name}',) + (str(value),) * (value is not True)
            for name, value in kwargs.items()
        )
    )


def checkout(project, target: path.Path = path.Path(), **kwargs):
    url = resolve(project)
    cmd = ['git', '-C', target, 'clone', url] + make_args(**kwargs)
    subprocess.check_call(cmd)
    repo = target / posixpath.basename(project)
    configure_fork(project, repo)
    return repo


def projects():
    """
    Load projects from PROJECTS_LIST_URL.
    """
    text = requests.get(os.environ['PROJECTS_LIST_URL']).text
    return set(map(Project.parse, text.splitlines()))


def exists(project, target):
    return target.joinpath(posixpath.basename(resolve(project))).isdir()


def checkout_missing(project, root):
    target = target_for_root(project, root)
    if exists(project, target):
        return
    target.mkdir_p()
    checkout(project, target)


@contextlib.contextmanager
def temp_checkout(project, **kwargs):
    kwargs.setdefault("depth", 50)
    with path.TempDir() as dir:
        repo = checkout(project, dir, **kwargs)
        with repo:
            yield
