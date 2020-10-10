import autocommand

from . import github
from . import repo


@autocommand.autocommand(__name__)
def run(project: github.Repo = github.Repo.detect()):
    md = repo.get_project_metadata()
    tag = 'v' + md.version
    project.create_release(tag)
