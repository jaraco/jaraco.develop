import functools
from typing import Annotated

import path
import typer
from jaraco.ui.main import main
from more_itertools import consume

from . import git


@main
def run(target: Annotated[path.Path, typer.Argument(parser=path.Path)] = path.Path()):
    checkout = functools.partial(git.checkout_missing, root=target)
    consume(map(checkout, git.projects()))
