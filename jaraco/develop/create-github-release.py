import sys
import subprocess
import urllib.parse

import autocommand

from . import github


@autocommand.autocommand(__name__)
def run():
    session = github.get_session()
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
