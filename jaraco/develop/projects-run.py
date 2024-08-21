"""
Routine to run a command across all projects.
"""

import functools
import subprocess
from typing import List

import typer
from typing_extensions import Annotated

from jaraco.ui.main import main

from . import filters, git


@functools.partial(
    main,
    app=typer.Typer(
        context_settings=dict(allow_extra_args=True, ignore_unknown_options=True)
    ),
)
def run(
    tag: Annotated[
        List[filters.Tag], typer.Option('--tag', '-t', parser=filters.Tag)
    ] = [],
    keyword: Annotated[
        List[filters.Keyword],
        typer.Option('--keyword', '-k', parser=filters.Keyword),
    ] = [],
    *,
    ctx: typer.Context,
):
    selectors = filters.Selectors(tag + keyword)
    for project in filter(selectors, git.projects()):
        print(project, flush=True)
        with git.temp_checkout(project, quiet=True):
            subprocess.Popen(ctx.args).wait()
        print(flush=True)
