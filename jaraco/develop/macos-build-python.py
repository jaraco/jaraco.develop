import os
import subprocess


def brew_prefix(name):
    cmd = ['brew', '--prefix', name]
    return subprocess.check_output(cmd, universal_newlines=True).strip()


def build_on_macOS():
    """
    Build cpython in the current directory on a mac with
    zlib and openssl installed.
    """
    zlib = brew_prefix('zlib')
    openssl = brew_prefix('openssl@1.1')
    includes = [
        f'{openssl}/include',
        f'{zlib}/include',
    ]
    libs = [
        f'{openssl}/lib',
        f'{zlib}/lib',
    ]

    env = dict(
        os.environ,
        CPPFLAGS=' '.join(f'-I{incl}' for incl in includes),
        LDFLAGS=' '.join(f'-L{lib}' for lib in libs),
    )
    subprocess.run(
        ['./configure', f'--with-openssl={openssl}'], env=env,
    )
    subprocess.run('make')


__name__ == '__main__' and build_on_macOS()
