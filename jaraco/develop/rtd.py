import functools

from requests_toolbelt import sessions

from . import secrets

url = 'https://readthedocs.org/'


@functools.lru_cache
def session():
    auth = secrets.Secret('Token ' + secrets.get_password(url, 'token'))
    session = sessions.BaseUrlSession(url + 'api/v3/')
    session.headers = dict(Authorization=auth)
    return session


def enable_pr_build(project):
    slug = project.replace('.', '').replace('_', '-')
    session().patch(f'projects/{slug}/', data=dict(external_builds_enabled=True))
