import autocommand

from . import github
from . import repo


@autocommand.autocommand(__name__)
def run(name, value):
    session = github.get_session()
    md = repo.get_project_metadata()
    secrets = f'{md.project}/secrets/{name}'
    params = dict(
        encrypted_value=github.encrypt(value),
        key_id=github.get_public_key().id,
    )
    resp = session.put(secrets, json=params)
    resp.ok or print(resp.text)
    resp.raise_for_status()
