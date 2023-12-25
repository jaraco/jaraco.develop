import os
import subprocess
import urllib.request

import pytest


def pytest_configure():
    os.environ['GITHUB_TOKEN'] = 'abc'


@pytest.fixture(autouse=True)
def git_url_substitutions(tmp_home_dir):
    """
    Configure Git to have substitutions for gh:// and gist://
    """
    subs = {
        'gh': 'https://github.com/',
        'gist': 'https://gist.github.com/',
    }
    for scheme, url in subs.items():
        cmd = ['git', 'config', '--global', f'url.{url}.insteadof', f'{scheme}://']
        subprocess.check_call(cmd)


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
