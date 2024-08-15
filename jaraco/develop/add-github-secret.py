import typer
from typing_extensions import Annotated
from jaraco.ui.main import main

from . import github


@main
def run(
    name,
    value,
    project: Annotated[
        github.Repo, typer.Option(parser=github.Repo)
    ] = github.Repo.detect(),
):
    project.add_secret(name, value)
