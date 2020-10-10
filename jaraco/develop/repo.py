import sys
import subprocess
import urllib.parse

import munch


def get_project_metadata():
    url, version = subprocess.run(
        [sys.executable, 'setup.py', '--url', '--version'],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.split()
    project = urllib.parse.urlparse(url).path.strip('/')
    return munch.Munch(locals())
