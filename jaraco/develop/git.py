import functools
import subprocess
import posixpath
import urllib.parse
import importlib.resources as res

import path

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


def checkout(project, target: path.Path = path.Path()):
    url = resolve(project)
    cmd = ['git', '-C', target, 'clone', url]
    subprocess.check_call(cmd)
    return target / posixpath.basename(project)


def projects():
    source = res.files('jaraco.develop').joinpath('projects.txt')
    return source.read_text().split()


def exists(project, target):
    return target.joinpath(posixpath.basename(resolve(project))).isdir()
