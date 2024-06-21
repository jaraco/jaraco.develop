import functools

import keyring
from requests_toolbelt import sessions

url = 'https://readthedocs.org/'


@functools.lru_cache
def session():
    auth = 'Token ' + keyring.get_password(url, 'token')
    session = sessions.BaseUrlSession(url + 'api/v3/')
    session.headers = dict(Authorization=auth)
    return session


def enable_pr_build(project):
    slug = project.replace('.', '').replace('_', '-')
    session().patch(f'projects/{slug}/', data=dict(external_builds_enabled=True))
