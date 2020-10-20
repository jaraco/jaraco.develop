import sys
import subprocess
import urllib.parse

from jaraco.collections import ItemsAsAttributes

from .py36compat import subprocess_run_text


class Bunch(dict, ItemsAsAttributes):
    pass


def get_project_metadata():
    url, version = subprocess_run_text(
        [sys.executable, 'setup.py', '--url', '--version'],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout.split()
    project = urllib.parse.urlparse(url).path.strip('/')
    return Bunch(locals())
