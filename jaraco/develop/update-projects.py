import contextlib
import subprocess
import importlib.resources as res

import path
import autocommand
from more_itertools import consume


def resolve(name):
    return 'jaraco/' * ('/' not in name) + name


@contextlib.contextmanager
def checkout(project):
    url = f'gh://{project}'
    with path.TempDir() as dir:
        repo = dir / 'repo'
        repo.mkdir()
        subprocess.check_call(['git', 'clone', url, repo])
        with repo:
            yield


def update_project(name):
    resolved = resolve(name)
    print('\nupdating', name)
    with checkout(resolved):
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
