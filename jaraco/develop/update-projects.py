"""
Mechanized merging of an upstream repo across all projects.

Relies on 'known-merge' tool, which must be configured with
git thus:

[mergetool "known-merge"]
cmd = py -m jaraco.develop.merge "$BASE" "$LOCAL" "$REMOTE" "$MERGED"
trustExitCode = true
"""

import contextlib
import subprocess
import functools
import shutil

import path
import autocommand
import subprocess_tee

from . import git


@contextlib.contextmanager
def temp_checkout(project):
    with path.TempDir() as dir:
        repo = git.checkout(project, dir, depth=50)
        with repo:
            yield


def handle_rename(old_name, new_name):
    status = subprocess.check_output(['git', 'status', '--porcelain'], text=True)
    if f'UD {old_name}' not in status:
        return
    shutil.copyfile(old_name, new_name)
    subprocess.check_call(['git', 'rm', old_name])
    subprocess.check_call(['git', 'add', new_name])


def update_project(name, base, branch=None):
    if set(name.tags) & {'fork', 'base'}:
        return
    print('\nupdating', name)
    with temp_checkout(name):
        cmd = ['git', 'pull', base, branch, '--no-edit']
        proc = subprocess_tee.run(list(filter(None, cmd)))
        if proc.returncode:
            if 'unrelated histories' in proc.stderr:
                return
            handle_rename('CHANGES.rst', 'NEWS.rst')
            try:
                subprocess.check_call(['git', 'mergetool', '-t', 'known-merge'])
            except subprocess.CalledProcessError:
                subprocess.check_call(['git', 'mergetool'])
            subprocess.check_call(['git', 'commit', '--no-edit'])
        subprocess.check_call(['git', 'push'])
        return name


class KeywordFilter(str):
    def __call__(self, other):
        return self in other


class TagFilter(str):
    def __call__(self, other):
        return self in other.tags


@autocommand.autocommand(__name__)
def main(
    keyword: KeywordFilter = None,  # type: ignore
    tag: TagFilter = None,  # type: ignore
    base='gh://jaraco/skeleton',
    branch=None,
):
    update = functools.partial(update_project, base=base, branch=branch)
    updates = map(update, filter(tag, filter(keyword, git.projects())))
    total = len(list(filter(None, updates)))
    print(f"Updated {total} projects.")
