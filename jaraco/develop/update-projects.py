import contextlib
import subprocess

import path
import autocommand
import jaraco.context
from more_itertools import consume

from . import git


@contextlib.contextmanager
def temp_checkout(project):
    with path.TempDir() as dir:
        repo = git.checkout(project, dir)
        with repo:
            yield


@jaraco.context.suppress(FileNotFoundError)
def is_skeleton():
    return 'badge/skeleton' in path.Path('README.txt').read_text()


def update_project(name):
    if name == 'skeleton':
        return
    print('\nupdating', name)
    with temp_checkout(name):
        if not is_skeleton():
            return
        proc = subprocess.Popen(['git', 'pull', 'gh://jaraco/skeleton'])
        code = proc.wait()
        if code:
            subprocess.check_call(['git', 'mergetool'])
            subprocess.check_call(['git', 'commit', '--no-edit'])
        subprocess.check_call(['git', 'push'])


@autocommand.autocommand(__name__)
def main():
    consume(map(update_project, git.projects()))
