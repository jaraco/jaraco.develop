import os
import textwrap

import pytest


def pytest_configure():
    os.environ['GITHUB_TOKEN'] = 'abc'


@pytest.fixture(autouse=True)
def git_url_substitutions(fake_process):
    cmd = ['git', 'config', '--get-regexp', r'url\..*\.insteadof']
    stdout = textwrap.dedent(
        """
        url.https://github.com/.insteadof gh://
        url.https://gist.github.com/.insteadof gist://
        """.lstrip()
    )

    fake_process.register(cmd, stdout=stdout)


@pytest.fixture(autouse=True)
def published_projects(monkeypatch):
    monkeypatch.setenv(
        'PROJECTS_LIST_URL',
        'https://raw.githubusercontent.com/jaraco/dotfiles/main/projects.txt',
    )


@pytest.fixture(autouse=True)
def workaround_pypy_4021(monkeypatch):
    import importlib
    import platform

    if platform.python_implementation() != 'PyPy':
        return
    ssl = importlib.import_module('_cffi_ssl._stdssl')
    monkeypatch.setattr(ssl, 'print', lambda *args: None, raising=False)
