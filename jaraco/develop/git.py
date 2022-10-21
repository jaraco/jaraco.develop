import functools
import os
import pathlib
import posixpath
import re
import subprocess
import types
import urllib.parse

import requests
import path
from more_itertools import flatten

from . import github


class URLScheme:
    """
    >>> getfixture('git_url_substitutions')
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
    >>> p = Project.parse('foo-project [tag1] [tag2]')
    >>> p
    'foo-project'
    >>> p.tags
    ['tag1', 'tag2']
    """

    pattern = re.compile(r'(?P<name>\S+)\s*(?P<rest>.*)$')

    def __new__(self, value, **kwargs):
        return super().__new__(self, value)

    def __init__(self, value, **kwargs):
        vars(self).update(kwargs)

    @classmethod
    def parse(cls, line):
        match = types.SimpleNamespace(**cls.pattern.match(line).groupdict())
        tags = list(re.findall(r'\[(.*?)\]', match.rest))
        return cls(match.name, tags=tags)


def resolve(name):
    """
    >>> projects = list(map(resolve, projects()))
    >>> 'gh://jaraco/keyrings.firefox' in projects
    True
    >>> 'gh://pmxbot/pmxbot.nsfw' in projects
    True
    """
    default = URL(f'https://github.com/{github.username()}/')
    return default.join(name)


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


def checkout(project, target: path.Path = path.Path(), **kwargs):
    args = list(flatten((f'--{name}', str(value)) for name, value in kwargs.items()))
    url = resolve(project)
    cmd = ['git', '-C', target, 'clone', url] + args
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
