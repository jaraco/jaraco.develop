import pathlib
import textwrap
import subprocess

import packaging.version


def next_version():
    with open('CHANGES.rst') as strm:
        last_ver_str = next(strm).strip()
    last_ver = packaging.version.Version(last_ver_str)
    return f'{last_ver.major}.{last_ver.minor + 1}.0'


def add_changelog():
    next_ver = next_version()
    underline = '=' * (len(next_ver) + 1)
    content = textwrap.dedent(
        f"""
        v{next_ver}
        {underline}

        Switched to PEP 420 for ``jaraco`` namespace.

        """
    ).lstrip()
    changes = pathlib.Path('CHANGES.rst')
    content += changes.read_text()
    changes.write_text(content)


def run():
    add_changelog()
    pathlib.Path('jaraco/__init__.py').unlink()
    subprocess.run(
        [
            'git',
            'commit',
            '-a',
            '-m',
            'Switch to PEP 420 namespace package',
        ]
    )


__name__ == '__main__' and run()
