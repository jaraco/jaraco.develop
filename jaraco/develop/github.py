import os
import getpass
import base64
import functools
import re
import pathlib
import itertools

import keyring
import nacl.public
import nacl.encoding
from requests_toolbelt import sessions

from . import repo


class Key(str):
    pass


class Repo(str):
    def __init__(self, name):
        self.session = self.get_session()

    @classmethod
    @functools.lru_cache()
    def get_session(cls):
        session = sessions.BaseUrlSession('https://api.github.com/repos/')
        session.headers.update(
            Accept='application/vnd.github.v3+json',
            Authorization=f'token {cls.load_token()}',
        )
        return session

    @staticmethod
    def load_token():
        token = os.environ.get("GITHUB_TOKEN") or keyring.get_password(
            'Github',
            username(),
        )
        assert token, "Token not available"
        return token

    @classmethod
    def detect(cls):
        return cls(repo.get_project_metadata().project)

    @functools.lru_cache()
    def get_public_key(self):
        data = self.session.get(f'{self}/actions/secrets/public-key').json()
        key = Key(data['key'])
        key.id = data['key_id']
        return key

    def encrypt(self, value):
        src = self.get_public_key().encode('utf-8')
        pub_key = nacl.public.PublicKey(src, nacl.encoding.Base64Encoder())
        box = nacl.public.SealedBox(pub_key)
        cipher_text = box.encrypt(value.encode('utf-8'))
        return base64.b64encode(cipher_text).decode('utf-8')

    def add_secret(self, name, value):
        secret = f'{self}/actions/secrets/{name}'
        params = dict(
            encrypted_value=self.encrypt(value),
            key_id=self.get_public_key().id,
        )
        resp = self.session.put(secret, json=params)
        resp.raise_for_status()
        return resp

    def create_release(self, tag):
        releases = f'{self}/releases'
        resp = self.session.post(releases, json=dict(tag_name=tag, name=tag))
        resp.raise_for_status()
        return resp

    @classmethod
    def find_needed_secrets(cls):
        """
        >>> list(Repo.find_needed_secrets())
        ['PYPI_TOKEN']
        """
        workflows = pathlib.Path('.github/workflows').iterdir()
        all = itertools.chain.from_iterable(map(cls.find_secrets, workflows))
        return itertools.filterfalse('GITHUB_TOKEN'.__eq__, all)

    @staticmethod
    def find_secrets(file):
        return (
            match.group(1)
            for match in re.finditer(
                r'\${{\s*secrets\.(\w+)\s*}}', file.read_text(encoding='utf-8')
            )
        )

    def get_metadata(self):
        """
        Get repository metadata.

        https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#get-a-repository

        >>> Repo('jaraco/pip-run').get_metadata()['description']
        'pip-run - dynamic dependency loader for Python'
        """
        resp = self.session.get(self)
        resp.raise_for_status()
        return resp.json()

    def update_metadata(self, **kwargs):
        """
        Update repository metadata (without overwriting existing keys).

        Some useful metadata keys:
        - name (str)
        - description (str)
        - homepage (str)
        - visibility ("public" or "private")
        - has_issues (bool)
        - default_branch (str)
        - archived (bool)
        - allow_forking (bool)

        See docs for all of them: https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#update-a-repository--parameters

        >>> Repo('jaraco/dead-parrot').update(
        ...     description="It's no more",
        ...     homepage='https://youtu.be/4vuW6tQ0218',
        ... )
        <Response [200]>
        """
        resp = self.session.patch(self, json=kwargs)
        resp.raise_for_status()
        return resp

    def get_topics(self):
        """
        Get topics for the repository.

        >>> Repo('jaraco/irc').get_topics()
        ['irc', 'python']
        """
        resp = self.session.get(self + '/topics')
        resp.raise_for_status()
        return resp.json()['names']

    def set_topics(self, *topics):
        """Completely replace the existing topics with only the given ones."""
        resp = self.session.put(self + '/topics', json=dict(names=topics))
        resp.raise_for_status()
        return resp

    def add_topics(self, *topics):
        """Add new topics to the repository, without removing existing ones."""
        return self.set_topics(*self.get_topics(), *topics)


def username():
    return os.environ.get('GITHUB_USERNAME') or getpass.getuser()
