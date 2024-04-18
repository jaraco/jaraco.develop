import pathlib
import re
import subprocess

import autocommand
from ini2toml.api import Translator


def split_build_system(pyproject):
    """
    Return the first section up to the second section, and the rest.
    """
    # put the toml ahead of the second section
    section_starts = re.finditer(r'^\[', pyproject, re.MULTILINE)
    _, second = next(section_starts), next(section_starts)
    return pyproject[: second.start()], pyproject[second.start() :]


def tweak(config):
    """
    Tweak the syntax some for easier merging with skeleton.
    """
    # convert single-line authors/maintainers to multiline
    config = re.sub(
        r'^(authors|maintainers) = \[(\{.*?\})\]',
        r'\1 = [\n\t\2,\n]',
        config,
        flags=re.MULTILINE | re.DOTALL,
    )
    config = re.sub(
        r'{(name = .*?")}', r'{ \1 }', config, flags=re.MULTILINE | re.DOTALL
    )
    config = re.sub(r'^    ', '\t', config, flags=re.MULTILINE)
    homepage = re.search('Homepage = ".*"', config).group(0)
    config = re.sub(r'^urls =.*?\n', '', config, flags=re.MULTILINE)
    if 'Homepage' not in config:
        homepage_scn = f'[project.urls]\n{homepage}\n\n'
        config = re.sub(
            r'(\[project\.optional-dependencies\])', homepage_scn + r'\1', config
        )
    config = re.sub(
        r'(\n\[tool\.setuptools\]\ninclude-package-data = true\n)',
        '',
        config,
        flags=re.MULTILINE,
    )
    config = re.sub(r'^\t# (local|tidelift)', r'\n\t# \1', config, flags=re.MULTILINE)
    return config


def bump_setuptools(build_system):
    return build_system.replace('setuptools>=56', 'setuptools>=61.2')


@autocommand.autocommand(__name__)
def run():
    pyproject = pathlib.Path('pyproject.toml')
    config = Translator().translate(pathlib.Path('setup.cfg').read_text(), 'setup.cfg')
    config_bs, config_rest = split_build_system(config)
    existing_bs, existing_rest = split_build_system(pyproject.read_text())
    pyproject.write_text(
        bump_setuptools(existing_bs) + tweak(config_rest) + '\n' + existing_rest
    )
    subprocess.check_call('git rm setup.cfg'.split())
    message = (
        "Migrated config to pyproject.toml using jaraco.develop.migrate-config "
        "and ini2toml."
    )
    subprocess.check_call(['git', 'commit', '-a', '-m', message])
