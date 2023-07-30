import pathlib
import subprocess

import autocommand

from . import towncrier


@autocommand.autocommand(__name__)
def finalize():
    ver = towncrier.semver(towncrier.get_version())
    # workaround for twisted/towncrier#538
    pathlib.Path('newsfragments').mkdir(exist_ok=True)
    towncrier.run('build', '--yes')
    subprocess.check_call(['git', 'commit', '-a', '-m' 'Finalize'])
    subprocess.check_call(['git', 'tag', '-a', '-m', '', ver])
