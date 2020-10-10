import autocommand

from . import github
from . import repo


@autocommand.autocommand(__name__)
def run():
    session = github.get_session()
    md = repo.get_project_metadata()
    tag = 'v' + md.version
    releases = f'{md.project}/releases'
    resp = session.post(releases, json=dict(tag_name=tag, name=tag))
    resp.ok or print(resp.text)
    resp.raise_for_status()
