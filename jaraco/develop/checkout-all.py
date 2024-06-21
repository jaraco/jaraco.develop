import functools

import autocommand
import path
from more_itertools import consume

from . import git


@autocommand.autocommand(__name__)
def main(target: path.Path = path.Path()):
    checkout = functools.partial(git.checkout_missing, root=target)
    consume(map(checkout, git.projects()))
