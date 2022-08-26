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
        subprocess.Popen(['git', 'clone', url, repo]).wait()
        with repo:
            yield


def update_project(name):
    resolved = resolve(name)
    with checkout(resolved):
        subprocess.Popen(['git', 'pull', 'gh://jaraco/skeleton']).wait()
        subprocess.Popen(['git', 'mergetool']).wait()
        subprocess.Popen(['git', 'push']).wait()


@autocommand.autocommand(__name__)
def main():
    source = res.files('jaraco.develop').joinpath('projects.txt')
    projects = source.read_text().split()
    consume(map(update_project, projects))
