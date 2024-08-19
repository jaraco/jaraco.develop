import getpass

import keyring
import typer
from typing_extensions import Annotated

import jaraco.context
from jaraco.ui.main import main

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


@main
def run(
    project: Annotated[
        github.Repo, typer.Option(parser=github.Repo)
    ] = github.Repo.detect(),
):
    for name in project.find_needed_secrets():
        source = secret_sources[name]
        value = keyring.get_password(**source)
        project.add_secret(name, value)
