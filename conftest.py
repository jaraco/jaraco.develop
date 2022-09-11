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
