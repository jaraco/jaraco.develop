import sys
import subprocess
import urllib.parse

import munch

from .py36compat import subprocess_run_text


def get_project_metadata():
    url, version = subprocess_run_text(
        [sys.executable, 'setup.py', '--url', '--version'],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout.split()
    project = urllib.parse.urlparse(url).path.strip('/')
    return munch.Munch(locals())
