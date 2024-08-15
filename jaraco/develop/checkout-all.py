import functools

import path
from jaraco.ui.main import main
from more_itertools import consume

from . import git


@main
def run(target: path.Path = path.Path()):
    checkout = functools.partial(git.checkout_missing, root=target)
    consume(map(checkout, git.projects()))
