import os
import textwrap

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
def published_projects(monkeypatch):
    monkeypatch.setenv(
        'PROJECTS_LIST_URL',
        'https://www.dropbox.com/s/g16c8w9i7lg9dqn/projects.txt?dl=1',
    )
