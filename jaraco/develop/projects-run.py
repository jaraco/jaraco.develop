"""
Routine to run a command across all projects.
"""

import subprocess

import autocommand

from . import filters
from . import git


@autocommand.autocommand(__name__)
def main(
    keyword: filters.Keyword = None,  # type: ignore
    tag: filters.Tag = None,  # type: ignore
    *args,
):
    for project in filter(tag, filter(keyword, git.projects())):
        print(project)
        with git.temp_checkout(project, quiet=True):
            subprocess.Popen(args).wait()
        print()
