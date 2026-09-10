"""
Routine to run a command across all projects.
"""

import functools
import itertools
import subprocess
from typing import Annotated

import typer
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
        list[filters.Tag] | None, typer.Option('--tag', '-t', parser=filters.Tag)
    ] = None,
    keyword: Annotated[
        list[filters.Keyword] | None,
        typer.Option('--keyword', '-k', parser=filters.Keyword),
    ] = None,
    *,
    ctx: typer.Context,
):
    selectors = filters.Selectors(itertools.chain(tag or (), keyword or ()))
    for project in filter(selectors, git.projects()):
        print(project, flush=True)
        with git.temp_checkout(project, quiet=True):
            subprocess.Popen(ctx.args).wait()
        print(flush=True)
