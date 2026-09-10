"""
Protection for secret values against incidental disclosure.
"""

import keyring
from jaraco.functools import pass_none


class Secret(str):
    """
    A string whose repr elides the value.

    Typer renders tracebacks through Rich, which presents the locals of
    each frame using repr, disclosing any secret those locals hold
    (jaraco/jaraco.develop#32). A Secret behaves as its value but
    declines to reveal it when represented.

    >>> token = Secret('sekrit')
    >>> token
    <Secret>
    >>> token.encode('utf-8')
    b'sekrit'
    >>> {'token': token}
    {'token': <Secret>}

    The value remains available to anything that asks for the string
    itself, so derived values are unprotected unless also wrapped.

    >>> print(token)
    sekrit
    >>> f'Bearer {token}'
    'Bearer sekrit'
    """

    __slots__ = ()

    def __repr__(self):
        return '<Secret>'


def get_password(*args, **kwargs):
    """
    Retrieve a password from keyring, wrapped as a Secret.

    Returns None when keyring has no such password.
    """
    return pass_none(Secret)(keyring.get_password(*args, **kwargs))
