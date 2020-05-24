import re


def to_spaces(script):
    r"""
    Replace tab indentation with space indentation.

    >>> to_spaces("\tfoo")
    '    foo'
    """
    return re.sub(r'^\t+', tabs_to_spaces, script, flags=re.MULTILINE)


def tabs_to_spaces(tabs):
    return ' ' * 4 * len(tabs.group(0))
