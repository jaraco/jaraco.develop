import os
import getpass
import base64
import functools

import keyring
import nacl.public
import nacl.encoding
from requests_toolbelt import sessions

from . import repo


session = sessions.BaseUrlSession('https://api.github.com/repos/')


def load_token():
    token = os.environ.get("GITHUB_TOKEN") or keyring.get_password(
        'Github', getpass.getuser()
    )
    assert token, "Token not available"
    return token


def get_session():
    session = sessions.BaseUrlSession('https://api.github.com/repos/')
    session.headers.update(
        Accept='application/vnd.github.v3+json',
        Authorization=f'token {load_token()}',
    )
    return session


class Key(str):
    pass


class Repo(str):
    @classmethod
    def detect(cls):
        return cls(repo.get_project_metadata().project)

    @functools.lru_cache
    def get_public_key(self):
        data = get_session().get(f'{self}/actions/secrets/public-key').json()
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
        resp = session.put(secret, json=params)
        resp.raise_for_status()
        return resp
