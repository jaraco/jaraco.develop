"""
Protection for secret values against incidental disclosure.
"""

import keyring
from jaraco.functools import compose, pass_none


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


get_password = compose(pass_none(Secret), keyring.get_password)
"""
Retrieve a password from keyring as a Secret, or None if unset.
"""
