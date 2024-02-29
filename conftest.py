import os
import textwrap
import urllib.request

import pytest


def pytest_configure():
    os.environ['GITHUB_TOKEN'] = 'abc'


@pytest.fixture
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
def published_projects(monkeypatch, tmp_path):
    """
    Generate a project list and set the environment variable.
    """
    projects = tmp_path / 'projects.txt'
    sample_projects = [
        '/pmxbot/pmxbot.nsfw',
        '/pypa/setuptools [lifted]',
        '/python/cpython [fork]',
        'jaraco.develop',
        'keyring [lifted]',
        'keyrings.firefox',
    ]
    projects.write_text('\n'.join(sample_projects), encoding='utf-8')
    url_path = urllib.request.pathname2url(str(projects))
    monkeypatch.setenv('PROJECTS_LIST_URL', f'file://{url_path}')


@pytest.fixture(autouse=True)
def workaround_pypy_4021(monkeypatch):
    import importlib
    import platform

    if platform.python_implementation() != 'PyPy':
        return
    ssl = importlib.import_module('_cffi_ssl._stdssl')
    monkeypatch.setattr(ssl, 'print', lambda *args: None, raising=False)
