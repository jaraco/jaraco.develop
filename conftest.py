import os


def pytest_configure():
    os.environ['GITHUB_TOKEN'] = 'abc'
