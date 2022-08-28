import autocommand
import path
import functools
import itertools
from more_itertools import consume

from . import git


@autocommand.autocommand(__name__)
def main(target: path.Path = path.Path()):
    checkout = functools.partial(git.checkout, target=target)
    exists = functools.partial(git.exists, target=target)
    missing = itertools.filterfalse(exists, git.projects())
    consume(map(checkout, missing))
