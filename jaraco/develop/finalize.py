import pathlib
import subprocess

from jaraco.ui.main import main

from . import towncrier


@main
def finalize():
    ver = towncrier.semver(towncrier.get_version())
    # workaround for twisted/towncrier#538
    pathlib.Path('newsfragments').mkdir(exist_ok=True)
    towncrier.run('build', '--yes')
    subprocess.check_call(['git', 'commit', '-a', '-m' 'Finalize'])
    subprocess.check_call(['git', 'tag', '-a', '-m', '', ver])
