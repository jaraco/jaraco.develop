from jaraco.ui.main import main

from . import github, repo


@main
def run(project: github.Repo = github.Repo.detect()):
    md = repo.get_project_metadata()
    project.create_release(tag=f'v{md.version}')
