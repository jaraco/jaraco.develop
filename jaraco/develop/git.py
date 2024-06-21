from __future__ import annotations

import contextlib
import functools
import os
import pathlib
import posixpath
import re
import subprocess
import types
import urllib.parse

import path
import requests
import requests_file
from more_itertools import flatten

from . import github
from .compat.py38 import removeprefix, removesuffix


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
        url = removesuffix(removeprefix(key, 'url.'), '.insteadof')
        return cls(scheme, url)

    def resolve(self, url):
        return url.replace(self.prefix, self.value)

    def apply(self, url):
        return url.replace(self.value, self.prefix)

    @classmethod
    @functools.lru_cache
    def load(cls):
        cmd = ['git', 'config', '--get-regexp', r'url\..*\.insteadof']
        lines = subprocess.run(
            cmd, capture_output=True, text=True, encoding='utf-8'
        ).stdout
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
    >>> p.spec
    'foo-project [tag1] [tag2]'
    """

    pattern = re.compile(r'(?P<name>\S+)\s*(?P<rest>.*)$')
    tags: list[str] = []

    def __new__(self, value, **kwargs):
        return super().__new__(self, value)

    def __init__(self, value, **kwargs):
        vars(self).update(kwargs)

    @classmethod
    def parse(cls, line):
        match = types.SimpleNamespace(**cls.pattern.match(line).groupdict())
        tags = list(re.findall(r'\[(.*?)\]', match.rest))
        return cls(match.name, tags=tags)

    @property
    def spec(self):
        return self + ''.join(map(' [{}]'.format, self.tags))


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
    # special case for calendra - make sure not to fetch tags from upstream.
    if project == 'calendra':
        cmd = 'git config remote.upstream.tagOpt --no-tags'.split()
        subprocess.check_output(cmd, cwd=repo)

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
    cmd = ['gh', 'repo', 'set-default', project.lstrip('/')]
    subprocess.check_call(cmd, cwd=repo)


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


def checkout(project: Project, target: path.Path = path.Path(), **kwargs):
    url = resolve(project)
    cmd = ['git', '-C', target, 'clone', url] + make_args(**kwargs)
    subprocess.check_call(cmd)
    repo = target / posixpath.basename(project)
    configure_fork(project, repo)
    return repo


@functools.lru_cache
def _session():
    """
    Return a requests session capable of opening files.
    """
    session = requests.Session()
    session.mount('file://', requests_file.FileAdapter())
    return session


def projects_repo():
    url = URL(os.environ['PROJECTS_LIST_URL'])
    project_path, inner_path = url.path.split('/main/')
    return Project(project_path), pathlib.Path(inner_path)


def projects():
    """
    Load projects from PROJECTS_LIST_URL.
    """
    text = _session().get(os.environ['PROJECTS_LIST_URL']).text
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
    with path.TempDir() as dir:
        repo = checkout(project, dir, depth=50, **kwargs)
        with repo:
            yield
