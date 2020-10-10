import os
import getpass

import keyring
from requests_toolbelt import sessions


session = sessions.BaseUrlSession('https://api.github.com/repos/')


def load_token():
    token = os.environ.get("GITHUB_TOKEN") or keyring.get_password(
        'Github', getpass.getuser()
    )
    assert token, "Token not available"
    return token


def get_session():
    session = sessions.BaseUrlSession('https://api.github.com/repos/')
    session.headers.update(
        Accept='application/vnd.github.v3+json',
        Authorization=f'token {load_token()}',
    )
    return session
