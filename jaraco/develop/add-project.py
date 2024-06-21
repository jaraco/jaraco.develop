"""
Add a repo to a list of projects maintained in GitHub.
"""

import operator
import subprocess

import autocommand
import path

import jaraco.text

from . import git


# TODO: move to jaraco.text
def add_newlines(lines):
    return map('{}\n'.format, lines)


@autocommand.autocommand(__name__)
def main(name: str, target: path.Path = path.Path()):
    repo, path = git.projects_repo()
    project = git.Project.parse(name)
    with git.temp_checkout(repo, quiet=True):
        projects = set(map(git.Project.parse, path.read_text().splitlines()))
        projects.add(project)
        specs = map(
            operator.attrgetter('spec'), sorted(projects, key=jaraco.text.FoldedCase)
        )
        path.write_text(''.join(add_newlines(specs)))
        subprocess.check_call(['git', 'commit', '-a', '-m', f'Adding {name}'])
        subprocess.check_call(['git', 'push'])
    git.checkout_missing(project, root=target)
