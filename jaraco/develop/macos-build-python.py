import os
import subprocess
import functools


@functools.lru_cache()
def brew_prefix(name):
    cmd = ['brew', '--prefix', name]
    return subprocess.check_output(cmd, text=True).strip()


def require_libs():
    reqs = 'gdbm', 'openssl@1.1', 'xz'
    cmd = ['brew', 'list']
    installed = subprocess.check_output(cmd, text=True).strip().split()
    assert set(reqs) < set(installed), "Need {missing}".format(
        missing=set(reqs) - set(installed))


def build_on_macOS():
    """
    Build cpython in the current directory on a mac with
    zlib and openssl installed.
    """
    require_libs()
    deps = 'zlib', 'openssl@1.1', 'xz'
    includes = [f'{prefix}/include' for prefix in map(brew_prefix, deps)]
    libs = [f'{prefix}/lib' for prefix in map(brew_prefix, deps)]
    env = dict(
        os.environ,
        CPPFLAGS=' '.join(f'-I{incl}' for incl in includes),
        LDFLAGS=' '.join(f'-L{lib}' for lib in libs),
    )
    openssl = brew_prefix('openssl@1.1')
    subprocess.run(
        ['./configure', f'--with-openssl={openssl}'], env=env,
    )
    subprocess.run('make')


__name__ == '__main__' and build_on_macOS()
