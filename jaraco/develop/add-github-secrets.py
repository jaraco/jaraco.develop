import autocommand
import keyring
import getpass

from . import github

secret_sources = {
    'PYPI_TOKEN': dict(
        username='__token__',
        service_name='https://upload.pypi.org/legacy/',
    ),
    'TIDELIFT_TOKEN': dict(
        username=getpass.getuser(),
        service_name='https://api.tidelift.com/external-api/',
    ),
}


@autocommand.autocommand(__name__)
def run(project: github.Repo = github.Repo.detect()):
    for name in project.find_needed_secrets():
        source = secret_sources[name]
        value = keyring.get_password(**source)
        project.add_secret(name, value)
