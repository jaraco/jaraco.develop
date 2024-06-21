import getpass

import autocommand
import keyring

import jaraco.context

from . import github


@jaraco.context.suppress(Exception)
def _safe_getuser():
    """
    getuser chokes by design in some environments.
    """
    return getpass.getuser()


secret_sources = {
    'PYPI_TOKEN': dict(
        username='__token__',
        service_name='https://upload.pypi.org/legacy/',
    ),
    'TIDELIFT_TOKEN': dict(
        username=_safe_getuser(),
        service_name='https://api.tidelift.com/external-api/',
    ),
    'WOLFRAMALPHA_API_KEY': dict(
        username=_safe_getuser(),
        service_name='https://api.wolframalpha.com/',
    ),
}


@autocommand.autocommand(__name__)
def run(project: github.Repo = github.Repo.detect()):
    for name in project.find_needed_secrets():
        source = secret_sources[name]
        value = keyring.get_password(**source)
        project.add_secret(name, value)
