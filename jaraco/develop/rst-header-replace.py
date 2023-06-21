import re
import sys

import autocommand


def replace_len(char):
    def replacer(match):
        size = len(match.group('heading'))
        return char * size

    return replacer


@autocommand.autocommand(__name__)
def run(before, after):
    assert len(before) == 1
    assert len(after) == 1
    for line in sys.stdin:
        repl = re.sub(
            f'^(?P<heading>({re.escape(before)})+)$',
            replace_len(after),
            line,
            flags=re.MULTILINE,
        )
        sys.stdout.write(repl)
