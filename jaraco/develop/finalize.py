import subprocess

import autocommand

from . import towncrier


@autocommand.autocommand(__name__)
def finalize():
    ver = towncrier.semver(towncrier.get_version())
    towncrier.run('build', '--yes')
    subprocess.check_call(['git', 'commit', '-a', '-m' 'Finalize'])
    subprocess.check_call(['git', 'tag', '-a', '-m', '', ver])
