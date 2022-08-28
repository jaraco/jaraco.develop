import autocommand
from more_itertools import consume

from . import git


@autocommand.autocommand(__name__)
def main():
    consume(map(git.checkout, git.projects()))
