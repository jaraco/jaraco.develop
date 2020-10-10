import autocommand

from . import github


@autocommand.autocommand(__name__)
def run(name, value, project: github.Repo = github.Repo.detect()):
    project.add_secret(name, value)
