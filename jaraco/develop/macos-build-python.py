"""
Build CPython according to
`the docs <https://devguide.python.org/setup/#macos-and-os-x>`_.
Assumes Homebrew is installed.
"""

import os
import subprocess
import functools

import autocommand


@functools.lru_cache()
def brew_prefix(name=None):
    cmd = ['brew', '--prefix']
    if name:
        cmd.append(name)
    return subprocess.check_output(cmd, text=True).strip()


def require_libs():
    reqs = 'gdbm', 'openssl@1.1', 'xz'
    cmd = ['brew', 'list']
    installed = subprocess.check_output(cmd, text=True).strip().split()
    assert set(reqs) < set(installed), "Need {missing}".format(
        missing=set(reqs) - set(installed)
    )


@autocommand.autocommand(__name__)
def build_on_macOS():
    """
    Build cpython in the current directory on a mac with
    zlib and openssl installed.
    """
    require_libs()

    env = dict(
        os.environ,
        CPPFLAGS=f'-I{brew_prefix()}/include',
        LDFLAGS=f'-I{brew_prefix()}/lib',
    )
    cmd = ['./configure', f'--with-openssl={brew_prefix("openssl@1.1")}']
    subprocess.run(cmd, env=env)
    subprocess.run('make')
