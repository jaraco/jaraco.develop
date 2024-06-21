"""
Routine to run a command across all projects.
"""

import argparse
import subprocess

import autocommand

from . import filters, git

parser = argparse.ArgumentParser()
parser.add_argument(
    '--keyword',
    '-k',
    dest='selectors',
    type=filters.Keyword,
    default=filters.Selectors(),
    action='append',
)
parser.add_argument(
    '--tag',
    '-t',
    dest='selectors',
    type=filters.Tag,
    default=filters.Selectors(),
    action='append',
)
parser.add_argument('args', nargs='*')


@autocommand.autocommand(__name__, parser=parser)
def main(
    selectors: filters.Selectors,
    args=None,
):
    for project in filter(selectors, git.projects()):
        print(project, flush=True)
        with git.temp_checkout(project, quiet=True):
            subprocess.Popen(args).wait()
        print(flush=True)
