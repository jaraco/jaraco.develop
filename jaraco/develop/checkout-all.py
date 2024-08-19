import functools

import path
from more_itertools import consume

from jaraco.ui.main import main

from . import git


@main
def run(target: path.Path = path.Path()):
    checkout = functools.partial(git.checkout_missing, root=target)
    consume(map(checkout, git.projects()))
