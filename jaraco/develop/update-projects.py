import contextlib
import subprocess

import path
import autocommand
from more_itertools import consume

from . import git


@contextlib.contextmanager
def temp_checkout(project):
    with path.TempDir() as dir:
        repo = git.checkout(project, dir)
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
    consume(map(update_project, git.projects()))
