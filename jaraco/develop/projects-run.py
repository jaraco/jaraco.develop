"""
Mechanized merging of an upstream repo across all projects.

Relies on 'known-merge' tool, which must be configured with
git thus:

[mergetool "known-merge"]
cmd = py -m jaraco.develop.merge "$BASE" "$LOCAL" "$REMOTE" "$MERGED"
trustExitCode = true
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
            subprocess.Popen(args)
        print()
