import os
import getpass
import contextlib
import subprocess
import posixpath
import importlib.resources as res

import path
import autocommand
from more_itertools import consume


def username():
    return os.environ.get('GITHUB_USERNAME', getpass.getuser())


def resolve(name):
    return f'{username()}/' * ('/' not in name) + name


def checkout(project, target: path.Path = path.Path()):
    url = f'gh://{resolve(project)}'
    cmd = ['git', 'clone', '-C', target, url]
    subprocess.check_call(cmd)
    return target / posixpath.basename(project)


@contextlib.contextmanager
def temp_checkout(project):
    with path.TempDir() as dir:
        repo = checkout(project, dir)
        with repo:
            yield


def update_project(name):
    print('\nupdating', name)
    with temp_checkout(name):
        proc = subprocess.Popen(['git', 'pull', 'gh://jaraco/skeleton'])
        code = proc.wait()
        if code:
            subprocess.check_call(['git', 'mergetool'])
            subprocess.check_call(['git', 'commit', '--no-edit'])
        subprocess.check_call(['git', 'push'])


@autocommand.autocommand(__name__)
def main():
    source = res.files('jaraco.develop').joinpath('projects.txt')
    projects = source.read_text().split()
    consume(map(update_project, projects))
