import autocommand

from . import github
from . import repo


@autocommand.autocommand(__name__)
def run(name, value):
    md = repo.get_project_metadata()
    github.Repo(md.project).add_secret(name, value)
