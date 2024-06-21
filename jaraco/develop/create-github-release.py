import autocommand

from . import github, repo


@autocommand.autocommand(__name__)
def run(project: github.Repo = github.Repo.detect()):
    md = repo.get_project_metadata()
    project.create_release(tag=f'v{md.version}')
