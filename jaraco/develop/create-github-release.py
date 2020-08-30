import os
import sys
import subprocess
import getpass
import urllib.parse

import keyring
import autocommand
from requests_toolbelt import sessions


session = sessions.BaseUrlSession('https://api.github.com/repos/')


def load_token():
    token = os.environ.get("GITHUB_TOKEN") or keyring.get_password(
        'Github', getpass.getuser()
    )
    assert token, "Token not available"
    return token


@autocommand.autocommand(__name__)
def run():
    session.headers.update(
        Accept='application/vnd.github.v3+json',
        Authorization=f'token {load_token()}',
    )
    url, version = subprocess.run(
        [sys.executable, 'setup.py', '--url', '--version'],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.split()
    tag = 'v' + version
    project = urllib.parse.urlparse(url).path.strip('/')
    releases = f'{project}/releases'
    resp = session.post(releases, json=dict(tag_name=tag, name=tag))
    resp.ok or print(resp.text)
    resp.raise_for_status()
