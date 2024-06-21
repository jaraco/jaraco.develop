"""
Build CPython according to
`the docs <https://devguide.python.org/setup/#macos-and-os-x>`_.
Assumes Homebrew is installed.
"""

import functools
import os
import subprocess

import autocommand


@functools.lru_cache
def brew_prefix(name=None):
    cmd = ['brew', '--prefix']
    if name:
        cmd.append(name)
    return subprocess.check_output(cmd, text=True).strip()


def require_libs():
    reqs = 'gdbm', 'openssl@3', 'xz'
    cmd = ['brew', 'list', '--formula']
    installed = subprocess.check_output(cmd, text=True).strip().split()
    missing = set(reqs) - set(installed)
    assert not missing, f"Need {missing}"


@autocommand.autocommand(__name__)
def build_on_macOS(debug=False):
    """
    Build cpython in the current directory on a mac with
    zlib and openssl installed.
    """
    require_libs()

    env = dict(
        os.environ,
        GDBM_CFLAGS=f"-I{brew_prefix('gdbm')}/include",
        GDBM_LIBS=f"-L{brew_prefix('gdbm')}/lib -lgdbm",
    )
    cmd = ['./configure']
    cmd += ['--with-pydebug'] * debug
    subprocess.run(cmd, env=env)
    subprocess.run(['make', '-j'])
